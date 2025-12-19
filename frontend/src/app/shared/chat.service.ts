import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { BehaviorSubject, Observable } from 'rxjs';

// Backend response interfaces matching your schemas
interface FinalAssessment {
  disease: string;
  severity: string;
  reason: string;
  explanation: string;
}

interface ChatResponse {
  session_id: string;
  finished: boolean;
  reply?: string;
  final?: FinalAssessment;
}

@Injectable({
  providedIn: 'root'
})
export class ChatService {
  private API_URL = 'http://127.0.0.1:8000/api';
  
  // Session management
  private currentSessionId: string | null = null;
  
  // Reset notifier - CHANGE TO PUBLIC
  public resetSubject = new BehaviorSubject<boolean>(false);
  reset$ = this.resetSubject.asObservable();

  constructor(private http: HttpClient) {}

  // Start new interview session
  startInterview(message: string): Observable<ChatResponse> {
    return this.http.post<ChatResponse>(`${this.API_URL}/start`, {
      message: message
    });
  }

  // Continue interview with session_id
  sendMessage(sessionId: string, message: string): Observable<ChatResponse> {
    return this.http.post<ChatResponse>(`${this.API_URL}/chat`, {
      session_id: sessionId,
      message: message
    });
  }

  // Reset chat session
  resetChat(sessionId: string): Observable<any> {
    return this.http.post(`${this.API_URL}/reset`, {
      session_id: sessionId
    });
  }

  // Store session ID
  setSessionId(sessionId: string) {
    this.currentSessionId = sessionId;
  }

  // Get current session ID
  getSessionId(): string | null {
    return this.currentSessionId;
  }

  // Clear session
  clearSession() {
    this.currentSessionId = null;
    this.resetSubject.next(true);
  }
}
