import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { BehaviorSubject, Observable } from 'rxjs';
import { tap } from 'rxjs/operators';

interface UserData {
  email: string;
  name?: string;
}

@Injectable({
  providedIn: 'root'
})
export class AuthService {
  private baseUrl = 'http://127.0.0.1:8000/api/auth';

  // 🆕 IN-MEMORY TOKEN CACHE (not localStorage)
  private tokenCache: string | null = null;

  // User data observable
  private userDataSubject = new BehaviorSubject<UserData | null>(null);
  public userData$ = this.userDataSubject.asObservable();

  constructor(private http: HttpClient) {
    // 🆕 Restore from sessionStorage on app init (survives page refresh, not browser close)
    this.tokenCache = sessionStorage.getItem('access_token');

    const userData = sessionStorage.getItem('user_data');
    if (userData) {
      this.userDataSubject.next(JSON.parse(userData));
    }
  }

  // =========================
  // 🆕 TOKEN CACHE METHODS
  // =========================

  setToken(token: string) {
    this.tokenCache = token;
    // Also store in sessionStorage for page refresh (cleared when browser closes)
    sessionStorage.setItem('access_token', token);
  }

  setUserData(data: UserData) {
    this.userDataSubject.next(data);
    sessionStorage.setItem('user_data', JSON.stringify(data));
  }

  getToken(): string | null {
    return this.tokenCache;
  }

  clearToken() {
    this.tokenCache = null;
    sessionStorage.removeItem('access_token');
    sessionStorage.removeItem('user_data');
  }

  // =========================
  // AUTH APIs
  // =========================

  login(email: string, password: string): Observable<any> {
    return this.http.post(`${this.baseUrl}/login`, { email, password }).pipe(
      tap((response: any) => {
        if (response.success && response.data?.access_token) {
          // 🆕 Store in cache
          this.setToken(response.data.access_token);

          // Fix: Capture name from backend response
          const name = response.data.user?.name || '';
          const userData = { email, name };

          this.userDataSubject.next(userData);
          sessionStorage.setItem('user_data', JSON.stringify(userData));

          console.log('✅ Token stored in cache');
        }
      })
    );
  }

  register(email: string, password: string, firstName: string, lastName: string, age: number, gender: string): Observable<any> {
    return this.http.post(`${this.baseUrl}/register`, {
      email,
      password,
      first_name: firstName,
      last_name: lastName,
      age: age,
      gender: gender
    }).pipe(
      tap((response: any) => {
        if (response.success && response.data?.access_token) {
          this.setToken(response.data.access_token);

          const fullName = `${firstName} ${lastName}`;
          const userData = { email, name: fullName };
          this.userDataSubject.next(userData);
          sessionStorage.setItem('user_data', JSON.stringify(userData));
        }
      })
    );
  }

  logout() {
    this.clearToken();
    this.userDataSubject.next(null);
    console.log('🚪 Logged out - token cleared from cache');
  }

  isLoggedIn(): boolean {
    return this.tokenCache !== null;
  }

  clearUser() {
    this.logout();
  }

  getUserEmail(): string | null {
    const userData = this.userDataSubject.value;
    return userData?.email || null;
  }
}
