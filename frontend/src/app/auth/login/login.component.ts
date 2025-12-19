import { Component } from '@angular/core';
import { Router } from '@angular/router';
import { AuthService } from '../../shared/auth.service';

@Component({
  selector: 'app-login',
  templateUrl: './login.component.html',
  styleUrls: ['./login.component.css']
})
export class LoginComponent {
  email = '';
  password = '';
  errorMessage = '';
  isLoading = false; // Add loading state

  constructor(
    private router: Router,
    private authService: AuthService
  ) {
    // Redirect if already logged in
    if (this.authService.isLoggedIn()) {
      this.router.navigate(['/chat']);
    }
  }

  login() {
    this.errorMessage = '';
    this.isLoading = true;

    // Validation
    if (!this.email || !this.password) {
      this.errorMessage = 'Please enter email and password';
      this.isLoading = false;
      return;
    }

    // Call backend API
    this.authService.login(this.email, this.password).subscribe({
      next: (response) => {
        this.isLoading = false;
        if (response.success) {
          console.log('Login successful:', response.user);
          this.router.navigate(['/chat']);
        }
      },
      error: (error) => {
        this.isLoading = false;
        console.error('Login error:', error);
        
        // Handle different error types
        if (error.status === 401) {
          this.errorMessage = 'Invalid email or password';
        } else if (error.status === 0) {
          this.errorMessage = 'Cannot connect to server. Is the backend running?';
        } else {
          this.errorMessage = error.error?.detail || 'Login failed. Please try again.';
        }
      }
    });
  }
}
