// import { Injectable } from '@angular/core';
// import { HttpClient, HttpParams, HttpHeaders } from '@angular/common/http';
// import { BehaviorSubject, Observable, throwError, of } from 'rxjs';
// import { catchError, tap } from 'rxjs/operators';
// import { Router } from '@angular/router';
// import { AuthService } from './auth.service';
 
 
// // Backend response interfaces
// interface FinalAssessment {
//   disease: string;
//   severity: string;
//   reason: string;
//   explanation: string;
// }
 
 
// interface ChatResponse {
//   session_id: string;
//   finished: boolean;
//   reply?: string;
//   final?: FinalAssessment;
// }
 
 
// interface SessionSummary {
//   session_id: string;
//   title: string;
//   status: string;
//   created_at: string;
//   updated_at: string;
//   completed_at?: string;
//   message_count: number;
// }
 
 
// interface MessageResponse {
//   message_id: number;
//   role: string;
//   content: string;
//   message_order: number;
//   created_at: string;
// }
 
 
// interface ConversationDetail {
//   session_id: string;
//   title: string;
//   status: string;
//   created_at: string;
//   messages: MessageResponse[];
//   assessment?: FinalAssessment;
// }
 
 
// interface GroupedHistory {
//   today: SessionSummary[];
//   yesterday: SessionSummary[];
//   this_week: SessionSummary[];
//   this_month: SessionSummary[];
//   older: SessionSummary[];
// }
 
 
// @Injectable({
//   providedIn: 'root'
// })
// export class ChatService {
//   private API_URL = 'http://127.0.0.1:8000/api';
//   private currentSessionId: string | null = null;
//   // Public observable for reset events
//   public resetSubject = new BehaviorSubject<boolean>(false);
//   reset$ = this.resetSubject.asObservable();
 
//   // History cache
//   private historyCache: GroupedHistory | null = null;
//   private historyCacheTime: number = 0;
//   private CACHE_DURATION = 10000; // 10 seconds
 
 
//   constructor(
//     private http: HttpClient,
//     private authService: AuthService,
//     private router: Router
//   ) {}
 
 
//   // Better auth header handling
//   private getAuthHeaders(): HttpHeaders {
//     const token = this.authService.getToken();
//     if (!token) {
//       console.error('No JWT token found');
//       this.router.navigate(['/login']);
//       throw new Error('Authentication required');
//     }
//     return new HttpHeaders({
//       'Authorization': `Bearer ${token}`,
//       'Content-Type': 'application/json'
//     });
//   }
 
 
//   // Global error handler
//   private handleError(error: any): Observable<never> {
//     console.error('API Error:', error);
//     if (error.status === 401) {
//       console.error('JWT token expired or invalid - redirecting to login');
//       this.authService.clearUser();
//       this.router.navigate(['/login']);
//     }
//     return throwError(() => error);
//   }
 
 
//   // =====================================================
//   // CHAT METHODS (JWT PROTECTED)
//   // =====================================================
//   startInterview(message: string): Observable<ChatResponse> {
//     const userData = this.authService.getUserData();
//     return this.http.post<ChatResponse>(
//       `${this.API_URL}/start`,
//       {
//         message: message,
//         user_email: userData?.email || ''
//       },
//       { headers: this.getAuthHeaders() }
//     ).pipe(
//       tap(() => this.clearHistoryCache()),
//       catchError(this.handleError.bind(this))
//     );
//   }
 
 
//   sendMessage(sessionId: string, message: string): Observable<ChatResponse> {
//     return this.http.post<ChatResponse>(
//       `${this.API_URL}/chat`,
//       {
//         session_id: sessionId,
//         message: message
//       },
//       { headers: this.getAuthHeaders() }
//     ).pipe(
//       tap(() => this.clearHistoryCache()),
//       catchError(this.handleError.bind(this))
//     );
//   }
 
 
//   resetChat(sessionId: string): Observable<any> {
//     return this.http.post(
//       `${this.API_URL}/reset`,
//       { session_id: sessionId },
//       { headers: this.getAuthHeaders() }
//     ).pipe(
//       tap(() => this.clearHistoryCache()),
//       catchError(this.handleError.bind(this))
//     );
//   }
 
 
//   setSessionId(sessionId: string) {
//     this.currentSessionId = sessionId;
//   }
 
 
//   getSessionId(): string | null {
//     return this.currentSessionId;
//   }
 
 
//   clearSession() {
//     this.currentSessionId = null;
//     this.resetSubject.next(true);
//     this.clearHistoryCache();
//   }
 
 
//   // =====================================================
//   // HISTORY METHODS - WITH CACHING
//   // =====================================================
 
 
//   getHistory(userEmail: string, limit: number = 50): Observable<SessionSummary[]> {
//     const params = new HttpParams()
//       .set('user_email', userEmail)
//       .set('limit', limit.toString());
//     return this.http.get<SessionSummary[]>(
//       `${this.API_URL}/history/`,
//       { 
//         params,
//         headers: this.getAuthHeaders()
//       }
//     ).pipe(
//       catchError(this.handleError.bind(this))
//     );
//   }
 
 
//   // With caching to reduce requests
//   getGroupedHistory(userEmail: string): Observable<GroupedHistory> {
//     // Return cached data if still valid
//     const now = Date.now();
//     if (this.historyCache && (now - this.historyCacheTime) < this.CACHE_DURATION) {
//       console.log('Using cached history');
//       return of(this.historyCache);
//     }
 
//     console.log('Fetching fresh history from API');
//     const params = new HttpParams().set('user_email', userEmail);
//     return this.http.get<GroupedHistory>(
//       `${this.API_URL}/history/grouped`,
//       { 
//         params,
//         headers: this.getAuthHeaders()
//       }
//     ).pipe(
//       tap(data => {
//         this.historyCache = data;
//         this.historyCacheTime = Date.now();
//         console.log('History cached');
//       }),
//       catchError(this.handleError.bind(this))
//     );
//   }
 
 
//   getConversation(sessionId: string, userEmail: string): Observable<ConversationDetail> {
//     const params = new HttpParams().set('user_email', userEmail);
//     return this.http.get<ConversationDetail>(
//       `${this.API_URL}/history/${sessionId}`,
//       { 
//         params,
//         headers: this.getAuthHeaders()
//       }
//     ).pipe(
//       catchError(this.handleError.bind(this))
//     );
//   }
 
 
//   deleteConversation(sessionId: string, userEmail: string): Observable<any> {
//     const params = new HttpParams().set('user_email', userEmail);
//     return this.http.delete(
//       `${this.API_URL}/history/${sessionId}`,
//       { 
//         params,
//         headers: this.getAuthHeaders()
//       }
//     ).pipe(
//       tap(() => this.clearHistoryCache()),
//       catchError(this.handleError.bind(this))
//     );
//   }
 
 
//   // Clear cache manually
//   clearHistoryCache() {
//     this.historyCache = null;
//     this.historyCacheTime = 0;
//     console.log('History cache cleared');
//   }
 
 
//   // Force refresh history (bypasses cache)
//   refreshHistory(userEmail: string): Observable<GroupedHistory> {
//     this.clearHistoryCache();
//     return this.getGroupedHistory(userEmail);
//   }
// }

import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { BehaviorSubject } from 'rxjs';

@Injectable({
  providedIn: 'root'
})
export class ChatService {
  private baseUrl = '/api';

  // session handling
  private sessionId: string | null = null;

  reset$ = new BehaviorSubject<boolean>(false);

  constructor(private http: HttpClient) {}

  // =========================
  // SESSION STATE
  // =========================
  setSessionId(id: string) {
    this.sessionId = id;
  }

  getSessionId(): string | null {
    return this.sessionId;
  }

  clearSession() {
    this.sessionId = null;
    this.reset$.next(true);
  }

  // =========================
  // CHAT
  // =========================
  startInterview(message: string) {
    return this.http.post(`${this.baseUrl}/start`, { message });
  }

  sendMessage(session_id: string, message: string) {
    return this.http.post(`${this.baseUrl}/chat`, { session_id, message });
  }

  resetChat(session_id: string) {
    return this.http.post(`${this.baseUrl}/reset`, { session_id });
  }

  // =========================
  // HISTORY
  // =========================
  getGroupedHistory() {
    return this.http.get(`${this.baseUrl}/history/grouped`);
  }

  getConversation(sessionId: string) {
    return this.http.get(`${this.baseUrl}/history/${sessionId}`);
  }

  deleteConversation(sessionId: string) {
    return this.http.delete(`${this.baseUrl}/history/${sessionId}`);
  }
}
