import { Component } from '@angular/core';
import { Router } from '@angular/router';
import { AuthService } from '../../shared/auth.service';

@Component({
  selector: 'app-signup',
  templateUrl: './signup.component.html',
  styleUrls: ['./signup.component.css']
})
export class SignupComponent {
  name = '';
  age!: number;
  gender = '';
  email = '';
  password = '';
  confirmPassword = '';
  errorMessage = '';
  isLoading = false;

  constructor(
    private router: Router,
    private authService: AuthService
  ) {}

  isValidName(name: string): boolean {
    return /^[A-Za-z ]+$/.test(name.trim());
  }

  signup() {
    this.errorMessage = '';

    // Validations
    if (!this.name || !this.isValidName(this.name)) {
      this.errorMessage = 'Please enter a valid name (letters only)';
      return;
    }

    if (!this.age || this.age <= 0 || this.age >= 120) {
      this.errorMessage = 'Please enter a valid age';
      return;
    }

    if (!this.gender) {
      this.errorMessage = 'Please select a gender';
      return;
    }

    if (!this.email || !this.email.includes('@')) {
      this.errorMessage = 'Please enter a valid email';
      return;
    }

    if (!this.password || this.password.length < 6) {
      this.errorMessage = 'Password must be at least 6 characters';
      return;
    }

    if (this.password !== this.confirmPassword) {
      this.errorMessage = 'Passwords do not match';
      return;
    }

    // Call backend API
    this.isLoading = true;
    
    console.log('Attempting registration...', this.email.toLowerCase());
    
    this.authService.register(
      this.name.trim(),
      this.age,
      this.gender,
      this.email.toLowerCase(),
      this.password
    ).subscribe({
      next: (response) => {
        console.log('Registration response:', response);
        this.isLoading = false;
        
        if (response.success) {
          console.log('User registered:', response.user);
          console.log('Token received:', response.access_token ? 'Yes' : 'No');
          
          // Check if token was stored
          const token = this.authService.getToken();
          console.log('Token in localStorage:', token ? 'Yes' : 'No');
          
          // Navigate to chat
          this.router.navigate(['/chat']);
        } else {
          this.errorMessage = response.message || 'Registration failed';
        }
      },
      error: (error) => {
        console.error('Registration error:', error);
        console.error('Error status:', error.status);
        console.error('Error detail:', error.error);
        
        this.isLoading = false;
        
        // Handle different error types
        if (error.status === 400) {
          this.errorMessage = error.error?.detail || 'Email already registered';
        } else if (error.status === 0) {
          this.errorMessage = 'Cannot connect to server. Is the backend running?';
        } else if (error.status === 500) {
          this.errorMessage = 'Server error. Please check backend logs.';
        } else {
          this.errorMessage = error.error?.detail || 'Registration failed. Please try again.';
        }
      }
    });
  }
}
