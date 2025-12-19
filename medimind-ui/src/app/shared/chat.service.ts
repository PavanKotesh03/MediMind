import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { BehaviorSubject } from 'rxjs';

@Injectable({
  providedIn: 'root'
})
export class ChatService {

  private API_URL = 'http://localhost:8000';

  // 🔥 reset notifier
  private resetSubject = new BehaviorSubject<boolean>(false);
  reset$ = this.resetSubject.asObservable();

  constructor(private http: HttpClient) {}

  sendMessage(message: string) {
    return this.http.post(`${this.API_URL}/chat`, {
      message
    });
  }

  resetChat() {
    this.http.post(`${this.API_URL}/chat/reset`, {})
      .subscribe(() => {
        this.resetSubject.next(true);
      });
  }
}
