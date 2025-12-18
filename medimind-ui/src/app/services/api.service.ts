import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';

@Injectable({
  providedIn: 'root'
})
export class ApiService {

  private baseUrl = 'http://localhost:8000';

  constructor(private http: HttpClient) {}

  checkBackend() {
    return this.http.get<{ status: string }>(`${this.baseUrl}/health`);
  }

  startChat(sessionId: string, message: string) {
  return this.http.post<any>(
    `${this.baseUrl}/api/v2/chat/start`,
    {
      session_id: sessionId,
      message: message
    }
  );
}
continueChat(sessionId: string, message: string) {
  return this.http.post<any>(
    `${this.baseUrl}/api/v2/chat`,
    {
      session_id: sessionId,
      message: message
    }
  );
}
}