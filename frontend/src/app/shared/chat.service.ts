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
      console.log('Restoring session from storage:', savedSession);
      this.sessionIdSubject.next(savedSession);
    }
  }

  setSessionId(id: string) {
    console.log('Storing session ID:', id);
    this.sessionIdSubject.next(id);
    sessionStorage.setItem('current_session_id', id);
  }

  getSessionId(): string | null {
    return this.sessionIdSubject.value;
  }

  clearSession() {
    console.log('Clearing session');
    this.sessionIdSubject.next(null);
    sessionStorage.removeItem('current_session_id');
    this.reset$.next(true);
  }

  startInterview(message: string): Observable<any> {
    console.log('API CALL: POST /start');
    return this.http.post(`${this.baseUrl}/start`, { message }).pipe(
      tap(() => this.clearCache())
    );
  }

  sendMessage(session_id: string, message: string): Observable<any> {
    console.log('API CALL: POST /chat');
    return this.http.post(`${this.baseUrl}/chat`, { session_id, message }).pipe(
      tap(() => this.invalidateConversationCache(session_id))
    );
  }

  resetChat(session_id: string): Observable<any> {
    console.log('API CALL: POST /reset');
    return this.http.post(`${this.baseUrl}/reset`, { session_id }).pipe(
      tap(() => this.clearCache())
    );
  }

  sendMessageStreaming(session_id: string, message: string): Observable<any> {
    return new Observable(observer => {
      const token = this.authService.getToken();
      
      if (!token) {
        console.error('No authentication token');
        observer.error({ error: 'No authentication token', type: 'error' });
        return;
      }

      const url = `${this.baseUrl}/chat/stream?session_id=${session_id}&message=${encodeURIComponent(message)}&token=${encodeURIComponent(token)}`;
      
      console.log('API CALL: GET /chat/stream');
      const eventSource = new EventSource(url);

      eventSource.onmessage = (event) => {
        if (event.data === '[DONE]') {
          console.log('Stream completed');
          eventSource.close();
          observer.complete();
          this.invalidateConversationCache(session_id);
          return;
        }

        try {
          const data = JSON.parse(event.data);
          
          if (data.type === 'error') {
            console.error('Stream error:', data.error);
            observer.error(data);
            eventSource.close();
            return;
          }
          
          observer.next(data);
        } catch (e) {
          console.error('Parse error:', e);
        }
      };

      eventSource.onerror = (error) => {
        console.error('SSE connection error:', error);
        eventSource.close();
        observer.error({ error: 'Connection failed', type: 'error' });
      };

      return () => {
        eventSource.close();
      };
    });
  }

  getGroupedHistory(): Observable<any> {
    const now = Date.now();
    
    if (this.historyCache && (now - this.historyCacheTime) < this.CACHE_DURATION) {
      console.log('Using cached history');
      return of(this.historyCache);
    }

    console.log('API CALL: GET /history/grouped');
    return this.http.get(`${this.baseUrl}/history/grouped`).pipe(
      tap((response: any) => {
        this.historyCache = response;
        this.historyCacheTime = Date.now();
        console.log('History cached');
      }),
      catchError(error => {
        console.error('History error:', error);
        throw error;
      })
    );
  }

  getConversation(sessionId: string): Observable<any> {
    if (this.conversationCache.has(sessionId)) {
      console.log('Using cached conversation:', sessionId);
      return of(this.conversationCache.get(sessionId));
    }

    console.log('API CALL: GET /history/' + sessionId);
    return this.http.get(`${this.baseUrl}/history/${sessionId}`).pipe(
      tap((response: any) => {
        this.conversationCache.set(sessionId, response);
        console.log('Conversation cached');
      }),
      catchError(error => {
        console.error('Conversation error:', error);
        throw error;
      })
    );
  }

  deleteConversation(sessionId: string): Observable<any> {
    console.log('API CALL: DELETE /history/' + sessionId);
    return this.http.delete(`${this.baseUrl}/history/${sessionId}`).pipe(
      tap(() => this.clearCache())
    );
  }

  clearCache() {
    this.historyCache = null;
    this.historyCacheTime = 0;
    this.conversationCache.clear();
    console.log('Cache cleared');
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
