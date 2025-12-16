import { Injectable } from '@angular/core';

@Injectable({ providedIn: 'root' })
export class AuthService {

  signup(user: any) {
    localStorage.setItem('medimind-user', JSON.stringify(user));
  }

  login(identifier: string, password: string): boolean {
    const user = JSON.parse(localStorage.getItem('medimind-user') || 'null');
    if (!user) return false;

    const valid =
      (user.email === identifier || user.phone === identifier) &&
      user.password === password;

    if (valid) {
      localStorage.setItem('current-user', 'true');
    }

    return valid;
  }

  saveDetails(details: any) {
    const user = JSON.parse(localStorage.getItem('medimind-user') || '{}');
    localStorage.setItem(
      'medimind-user',
      JSON.stringify({ ...user, ...details })
    );
  }

  getLoggedInUser() {
    const loggedIn = localStorage.getItem('current-user');
    if (!loggedIn) return null;

    return JSON.parse(localStorage.getItem('medimind-user') || 'null');
  }

  logout() {
    localStorage.removeItem('current-user');
  }
}
