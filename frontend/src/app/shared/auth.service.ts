import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { BehaviorSubject, Observable } from 'rxjs';
import { tap } from 'rxjs/operators';

interface User {
  name: string;
  email: string;
  age: number;
  gender: string;
}

interface AuthResponse {
  success: boolean;
  message: string;
  user: User | null;
  access_token?: string;  // ✅ MUST HAVE THIS
}

@Injectable({
  providedIn: 'root'
})
export class AuthService {
  private apiUrl = 'http://127.0.0.1:8000/api/auth';
  
  private userNameSubject = new BehaviorSubject<string>(
    localStorage.getItem('userName') || ''
  );

  private userDataSubject = new BehaviorSubject<User | null>(
    this.getUserDataFromStorage()
  );

  userName$ = this.userNameSubject.asObservable();
  userData$ = this.userDataSubject.asObservable();

  constructor(private http: HttpClient) {}

  // Register API call
  register(name: string, age: number, gender: string, email: string, password: string): Observable<AuthResponse> {
    return this.http.post<AuthResponse>(`${this.apiUrl}/register`, {
      name,
      age,
      gender,
      email,
      password
    }).pipe(
      tap(response => {
        console.log('Register response:', response);  // DEBUG
        if (response.success && response.user && response.access_token) {
          this.storeUserData(response.user, response.access_token);
        }
      })
    );
  }

  // Login API call
  login(email: string, password: string): Observable<AuthResponse> {
    return this.http.post<AuthResponse>(`${this.apiUrl}/login`, {
      email,
      password
    }).pipe(
      tap(response => {
        console.log('Login response:', response);  // DEBUG
        if (response.success && response.user && response.access_token) {
          this.storeUserData(response.user, response.access_token);
        }
      })
    );
  }

  // Store user data and JWT token
  private storeUserData(user: User, token: string) {
    console.log('Storing user data:', user);  // DEBUG
    console.log('Storing token:', token);     // DEBUG
    
    localStorage.setItem('userName', user.name);
    localStorage.setItem('userData', JSON.stringify(user));
    localStorage.setItem('access_token', token);
    
    this.userNameSubject.next(user.name);
    this.userDataSubject.next(user);
  }

  // Get user data from localStorage
  private getUserDataFromStorage(): User | null {
    const userData = localStorage.getItem('userData');
    return userData ? JSON.parse(userData) : null;
  }

  // Get current user data
  getUserData(): User | null {
    return this.userDataSubject.value;
  }

  // Get user email directly
  getUserEmail(): string {
    const user = this.getUserData();
    return user?.email || '';
  }

  // Get JWT token
  getToken(): string | null {
    return localStorage.getItem('access_token');
  }

  // Clear user data on logout
  clearUser() {
    localStorage.removeItem('userName');
    localStorage.removeItem('userData');
    localStorage.removeItem('access_token');
    this.userNameSubject.next('');
    this.userDataSubject.next(null);
  }

  // Check if user is logged in
  isLoggedIn(): boolean {
    return !!this.getToken();
  }
}
