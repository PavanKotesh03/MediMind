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
  age: number | null = null;  // ✅ Add back
  gender = '';                 // ✅ Add back
  email = '';
  password = '';
  confirmPassword = '';
  errorMessage = '';
  isLoading = false;

  constructor(
    private router: Router,
    private authService: AuthService
  ) { }

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

    // ✅ Register with just email, password, name (backend ignores age/gender for now)
    this.authService.register(
      this.email.toLowerCase(),
      this.password,
      this.name.trim()
    ).subscribe({
      next: (response) => {
        console.log('Registration response:', response);
        this.isLoading = false;

        if (response.success && response.data) {
          console.log('User registered successfully');
          this.router.navigate(['/chat']);
        } else {
          this.errorMessage = response.message || 'Registration failed';
        }
      },
      error: (error) => {
        console.error('Registration error:', error);
        this.isLoading = false;

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
