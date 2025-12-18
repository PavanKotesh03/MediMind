import { Component, EventEmitter, Output, OnInit } from '@angular/core';
import { ApiService } from '../../services/api.service';

@Component({
  selector: 'app-user-form',
  templateUrl: './user-form.component.html',
  styleUrls: ['./user-form.component.css']
})
export class UserFormComponent implements OnInit {

  // Form fields
  name = '';
  age!: number;
  gender = '';

  // State
  errorMessage = '';
  sessionId = '';

  // ⬇️ IMPORTANT: emit BOTH sessionId + first bot message
  @Output() startChat = new EventEmitter<{
    sessionId: string;
    firstMessage: string;
  }>();

  constructor(private apiService: ApiService) {}

  ngOnInit(): void {
    // Silent backend health check
    this.apiService.checkBackend().subscribe({
      next: () => {
        // backend reachable
      },
      error: () => {
        console.error('Backend not reachable');
      }
    });
  }

  // Name: letters and spaces only
  isValidName(name: string): boolean {
    return /^[A-Za-z ]+$/.test(name.trim());
  }

  submit() {
    console.log('Submit clicked');
    this.errorMessage = '';

    // Name validation
    if (!this.name || !this.isValidName(this.name)) {
      this.errorMessage = 'Please enter a valid name (letters only)';
      return;
    }

    // Age validation
    if (!this.age || this.age <= 0) {
      this.errorMessage = 'Please enter a valid age';
      return;
    }

    if (this.age >= 100) {
      this.errorMessage = 'Please enter a valid age below 100';
      return;
    }

    // Gender validation
    if (!this.gender) {
      this.errorMessage = 'Please select a gender';
      return;
    }

    console.log('Validation passed. Ready to call API');

    // ✅ Generate session ID ONCE
    this.sessionId = 'clinview-' + Date.now();

    // ✅ Call backend start chat API
    this.apiService.startChat(this.sessionId, this.name.trim())
      .subscribe({
        next: (response) => {
          console.log('ClinView response:', response);

          // ✅ Emit BOTH values to parent
          this.startChat.emit({
            sessionId: this.sessionId,
            firstMessage: response.response
          });
        },
        error: (err) => {
          console.error('Failed to start chat', err);
          this.errorMessage = 'Unable to start chat. Please try again.';
        }
      });
  }
}
