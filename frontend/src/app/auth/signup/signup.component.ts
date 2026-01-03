import { Component } from '@angular/core';
import { Router } from '@angular/router';
import { AuthService } from 'src/app/shared/auth.service';
import { NgForm } from '@angular/forms'; // Import NgForm

@Component({
  selector: 'app-signup',
  templateUrl: './signup.component.html',
  styleUrls: ['./signup.component.css']
})
export class SignupComponent {
  firstName = '';
  lastName = '';
  age: number | null = null;
  gender = '';
  email = '';
  password = '';
  confirmPassword = '';

  errors = {
    general: ''
  };

  isLoading = false;

  constructor(
    private router: Router,
    private authService: AuthService
  ) { }

  signup(form: NgForm) {
    // Reset general error
    this.errors.general = '';

    // If form is invalid or passwords don't match, touch all fields to show errors
    if (form.invalid || this.password !== this.confirmPassword) {
      Object.keys(form.controls).forEach(key => {
        form.controls[key].markAsTouched();
      });

      // Special case for password mismatch manual check
      if (this.password !== this.confirmPassword && form.controls['confirmPassword']) {
        form.controls['confirmPassword'].markAsTouched();
      }
      return;
    }

    // Call backend API
    this.isLoading = true;

    console.log('Attempting registration...', this.email.toLowerCase());

    this.authService.register(
      this.email.toLowerCase(),
      this.password,
      this.firstName.trim(),
      this.lastName.trim(),
      this.age || 0,
      this.gender
    ).subscribe({
      next: (response) => {
        console.log('Registration response:', response);
        this.isLoading = false;

        if (response.success && response.data) {
          console.log('User registered successfully');
          this.router.navigate(['/chat']);
        } else {
          this.errors.general = response.message || 'Registration failed';
        }
      },
      error: (error) => {
        console.error('Registration error:', error);
        this.isLoading = false;

        if (error.status === 400) {
          this.errors.general = error.error?.detail || 'Email already registered';
        } else if (error.status === 0) {
          this.errors.general = 'Cannot connect to server. Is the backend running?';
        } else if (error.status === 500) {
          this.errors.general = 'Server error. Please check backend logs.';
        } else {
          this.errors.general = error.error?.detail || 'Registration failed. Please try again.';
        }
      }
    });
  }
}
