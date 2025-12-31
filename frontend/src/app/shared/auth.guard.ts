import { Injectable } from '@angular/core';
import { CanActivate, Router } from '@angular/router';
import { AuthService } from './auth.service';

@Injectable({
  providedIn: 'root'
})
export class AuthGuard implements CanActivate {

  constructor(
    private authService: AuthService,
    private router: Router
  ) {}

  canActivate(): boolean {
    // Check if JWT token exists (using AuthService method)
    if (this.authService.isLoggedIn()) {
      console.log('AuthGuard: User authenticated');
      return true; // Allow access
    }

    // Block access and redirect to login
    console.log('AuthGuard: User not authenticated, redirecting to login');
    this.router.navigate(['/login']);
    return false;
  }
}
