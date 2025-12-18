import { Injectable } from '@angular/core';
import { BehaviorSubject } from 'rxjs';

@Injectable({
  providedIn: 'root'
})
export class AuthService {
  private userNameSubject = new BehaviorSubject<string>(
    localStorage.getItem('userName') || ''
  );

  userName$ = this.userNameSubject.asObservable();

  setUserName(name: string) {
    localStorage.setItem('userName', name);
    this.userNameSubject.next(name);
  }

  clearUser() {
    localStorage.removeItem('userName');
    this.userNameSubject.next('');
  }
}
