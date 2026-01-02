import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { BehaviorSubject, Observable, of } from 'rxjs';
import { tap, catchError } from 'rxjs/operators';
import { AuthService } from './auth.service';

@Injectable({
  providedIn: 'root'
})
export class ChatService {
  private baseUrl = 'http://127.0.0.1:8000/api';

  private sessionIdSubject = new BehaviorSubject<string | null>(null);
  public sessionId$ = this.sessionIdSubject.asObservable();
  
  reset$ = new BehaviorSubject<boolean>(false);

  private historyCache: any = null;
  private historyCacheTime: number = 0;
  private CACHE_DURATION = 30000;

  private conversationCache = new Map<string, any>();

  constructor(
    private http: HttpClient,
    private authService: AuthService
  ) {
    const savedSession = sessionStorage.getItem('current_session_id');
    if (savedSession) {
      console.log('SERVICE: Restored session:', savedSession);
      this.sessionIdSubject.next(savedSession);
    }
  }

  setSessionId(id: string) {
    console.log('SERVICE: Setting session ID:', id);
    this.sessionIdSubject.next(id);
    sessionStorage.setItem('current_session_id', id);
  }

  getSessionId(): string | null {
    return this.sessionIdSubject.value;
  }

  clearSession() {
    console.log('SERVICE: Clearing session');
    this.sessionIdSubject.next(null);
    sessionStorage.removeItem('current_session_id');
    // Don't trigger reset observable - causes issues
  }

  startInterview(message: string): Observable<any> {
    console.log('SERVICE: POST /start');
    return this.http.post(`${this.baseUrl}/start`, { message }).pipe(
      tap(() => this.clearCache())
    );
  }

  sendMessageStreaming(session_id: string, message: string): Observable<any> {
    return new Observable(observer => {
      const token = this.authService.getToken();
      
      if (!token) {
        console.error('SERVICE: No token');
        observer.error({ error: 'No authentication token', type: 'error' });
        return;
      }

      const url = `${this.baseUrl}/chat/stream?session_id=${session_id}&message=${encodeURIComponent(message)}&token=${encodeURIComponent(token)}`;
      
      console.log('SERVICE: GET /chat/stream');
      
      const eventSource = new EventSource(url);

      eventSource.onmessage = (event) => {
        if (event.data === '[DONE]') {
          console.log('SERVICE: Stream done');
          eventSource.close();
          observer.complete();
          this.invalidateConversationCache(session_id);
          return;
        }

        try {
          const data = JSON.parse(event.data);
          console.log('SERVICE: Stream chunk:', data);
          
          if (data.type === 'error') {
            console.error('SERVICE: Stream error:', data.error);
            observer.error(data);
            eventSource.close();
            return;
          }
          
          observer.next(data);
        } catch (e) {
          console.error('SERVICE: Parse error:', e);
        }
      };

      eventSource.onerror = (error) => {
        console.error('SERVICE: SSE error:', error);
        eventSource.close();
        observer.error({ error: 'Connection failed', type: 'error' });
      };

      return () => {
        console.log('SERVICE: Closing EventSource');
        eventSource.close();
      };
    });
  }

  resetChat(session_id: string): Observable<any> {
    console.log('SERVICE: POST /reset');
    return this.http.post(`${this.baseUrl}/reset`, { session_id }).pipe(
      tap(() => this.clearCache())
    );
  }

  getGroupedHistory(): Observable<any> {
    const now = Date.now();
    
    if (this.historyCache && (now - this.historyCacheTime) < this.CACHE_DURATION) {
      console.log('SERVICE: Cache hit');
      return of(this.historyCache);
    }

    console.log('SERVICE: GET /history/grouped');
    return this.http.get(`${this.baseUrl}/history/grouped`).pipe(
      tap((response: any) => {
        this.historyCache = response;
        this.historyCacheTime = Date.now();
      }),
      catchError(error => {
        console.error('SERVICE: History error:', error);
        throw error;
      })
    );
  }

  getConversation(sessionId: string): Observable<any> {
    if (this.conversationCache.has(sessionId)) {
      console.log('SERVICE: Cache hit for conversation');
      return of(this.conversationCache.get(sessionId));
    }

    console.log('SERVICE: GET /history/' + sessionId);
    return this.http.get(`${this.baseUrl}/history/${sessionId}`).pipe(
      tap((response: any) => {
        this.conversationCache.set(sessionId, response);
      }),
      catchError(error => {
        console.error('SERVICE: Conversation error:', error);
        throw error;
      })
    );
  }

  deleteConversation(sessionId: string): Observable<any> {
    console.log('SERVICE: DELETE /history/' + sessionId);
    return this.http.delete(`${this.baseUrl}/history/${sessionId}`).pipe(
      tap(() => this.clearCache())
    );
  }

  clearCache() {
    this.historyCache = null;
    this.historyCacheTime = 0;
    this.conversationCache.clear();
  }

  invalidateConversationCache(sessionId: string) {
    this.conversationCache.delete(sessionId);
    this.historyCache = null;
  }

  forceRefreshHistory(): Observable<any> {
    this.clearCache();
    return this.getGroupedHistory();
  }
}
