import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { BehaviorSubject, Observable, of, Subject } from 'rxjs';
import { tap, catchError } from 'rxjs/operators';
import { AuthService } from './auth.service';

@Injectable({
    providedIn: 'root'
})
export class ChatService {
    private baseUrl = 'http://127.0.0.1:8000/api';

    private sessionIdSubject = new BehaviorSubject<string | null>(null);
    public sessionId$ = this.sessionIdSubject.asObservable();

    private sidebarSubject = new BehaviorSubject<boolean>(false);
    public sidebarOpen$ = this.sidebarSubject.asObservable();

    reset$ = new Subject<boolean>();

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
            console.log('✅ Restoring session from storage:', savedSession);
            this.sessionIdSubject.next(savedSession);
        }
    }

    setSessionId(id: string) {
        console.log('💾 Storing session ID:', id);
        this.sessionIdSubject.next(id);
        sessionStorage.setItem('current_session_id', id);
    }

    getSessionId(): string | null {
        return this.sessionIdSubject.value;
    }

    clearSession() {
        console.log('🗑️ Clearing session');
        this.sessionIdSubject.next(null);
        sessionStorage.removeItem('current_session_id');
        this.reset$.next(true);
    }

    toggleSidebar() {
        this.sidebarSubject.next(!this.sidebarSubject.value);
    }

    // =====================================================
    // 🆕 START CHAT (STREAMING)
    // =====================================================
    startChat(
        message: string | null,
        onToken: (token: string) => void,
        onSessionId: (sessionId: string) => void,
        onComplete: (finished: boolean) => void,
        onError: (error: any) => void
    ): void {
        const token = this.authService.getToken();
        
        console.log('📡 Starting streaming chat...');

        fetch(`${this.baseUrl}/start`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${token}`
            },
            body: JSON.stringify({ message: message || null })
        })
        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            
            const reader = response.body?.getReader();
            const decoder = new TextDecoder();
            
            const readStream = () => {
                reader?.read().then(({ done, value }) => {
                    if (done) {
                        console.log('✅ Stream complete');
                        return;
                    }
                    
                    const chunk = decoder.decode(value, { stream: true });
                    const lines = chunk.split('\n');
                    
                    for (const line of lines) {
                        if (line.startsWith('data: ')) {
                            try {
                                const data = JSON.parse(line.substring(6));
                                
                                if (data.type === 'session_id') {
                                    console.log('🆔 Session ID received:', data.data);
                                    onSessionId(data.data);
                                } else if (data.type === 'token') {
                                    onToken(data.data);
                                } else if (data.type === 'finalizing') {
                                    // 🆕 Handle finalizing event
                                    onToken('\n\n' + data.data);
                                } else if (data.type === 'explanation_token') {
                                    // Handle explanation streaming
                                    onToken(data.data);
                                } else if (data.type === 'done') {
                                    console.log('✅ Stream done');
                                    onComplete(data.data.finished);
                                } else if (data.type === 'error') {
                                    console.error('❌ Stream error:', data.data);
                                    onError(data.data);
                                }
                            } catch (e) {
                                console.error('❌ Failed to parse SSE data:', e);
                            }
                        }
                    }
                    
                    readStream();
                }).catch(error => {
                    console.error('❌ Stream read error:', error);
                    onError(error);
                });
            };
            
            readStream();
        })
        .catch(error => {
            console.error('❌ Fetch error:', error);
            onError(error);
        });
    }

    // =====================================================
    // 🆕 SEND MESSAGE (STREAMING)
    // =====================================================
    sendMessage(
        session_id: string,
        message: string,
        onToken: (token: string) => void,
        onFinal: (final: any) => void,
        onComplete: (finished: boolean) => void,
        onError: (error: any) => void
    ): void {
        const token = this.authService.getToken();
        
        console.log('📡 Sending streaming message...');

        fetch(`${this.baseUrl}/chat`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${token}`
            },
            body: JSON.stringify({ session_id, message })
        })
        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            
            const reader = response.body?.getReader();
            const decoder = new TextDecoder();
            
            const readStream = () => {
                reader?.read().then(({ done, value }) => {
                    if (done) {
                        console.log('✅ Stream complete');
                        return;
                    }
                    
                    const chunk = decoder.decode(value, { stream: true });
                    const lines = chunk.split('\n');
                    
                    for (const line of lines) {
                        if (line.startsWith('data: ')) {
                            try {
                                const data = JSON.parse(line.substring(6));
                                
                                if (data.type === 'token') {
                                    onToken(data.data);
                                } else if (data.type === 'finalizing') {
                                    // 🆕 Handle finalizing event
                                    onToken('\n\n' + data.data);
                                } else if (data.type === 'explanation_token') {
                                    // 🆕 Handle explanation streaming
                                    onToken(data.data);
                                } else if (data.type === 'final') {
                                    console.log('🏁 Final assessment received');
                                    onFinal(data.data);
                                } else if (data.type === 'done') {
                                    console.log('✅ Stream done');
                                    onComplete(data.data.finished);
                                } else if (data.type === 'error') {
                                    console.error('❌ Stream error:', data.data);
                                    onError(data.data);
                                }
                            } catch (e) {
                                console.error('❌ Failed to parse SSE data:', e);
                            }
                        }
                    }
                    
                    readStream();
                }).catch(error => {
                    console.error('❌ Stream read error:', error);
                    onError(error);
                });
            };
            
            readStream();
        })
        .catch(error => {
            console.error('❌ Fetch error:', error);
            onError(error);
        });
    }

    // =====================================================
    // OTHER METHODS (KEEP THESE)
    // =====================================================
    resetChat(session_id: string): Observable<any> {
        console.log('📡 API CALL: POST /reset');
        return this.http.post(`${this.baseUrl}/reset`, { session_id }).pipe(
            tap(() => this.clearCache())
        );
    }

    getGroupedHistory(): Observable<any> {
        const now = Date.now();

        if (this.historyCache && (now - this.historyCacheTime) < this.CACHE_DURATION) {
            console.log('💾 Using cached history');
            return of(this.historyCache);
        }

        console.log('📡 API CALL: GET /history/grouped');
        return this.http.get(`${this.baseUrl}/history/grouped`).pipe(
            tap((response: any) => {
                this.historyCache = response;
                this.historyCacheTime = Date.now();
                console.log('✅ History cached');
            }),
            catchError(error => {
                console.error('❌ History error:', error);
                throw error;
            })
        );
    }

    getConversation(sessionId: string): Observable<any> {
        if (this.conversationCache.has(sessionId)) {
            console.log('💾 Using cached conversation:', sessionId);
            return of(this.conversationCache.get(sessionId));
        }

        console.log('📡 API CALL: GET /history/' + sessionId);
        return this.http.get(`${this.baseUrl}/history/${sessionId}`).pipe(
            tap((response: any) => {
                this.conversationCache.set(sessionId, response);
                console.log('✅ Conversation cached');
            }),
            catchError(error => {
                console.error('❌ Conversation error:', error);
                throw error;
            })
        );
    }

    deleteConversation(sessionId: string): Observable<any> {
        console.log('📡 API CALL: DELETE /history/' + sessionId);
        return this.http.delete(`${this.baseUrl}/history/${sessionId}`).pipe(
            tap(() => this.clearCache())
        );
    }

    clearCache() {
        this.historyCache = null;
        this.historyCacheTime = 0;
        this.conversationCache.clear();
        console.log('🗑️ Cache cleared');
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
