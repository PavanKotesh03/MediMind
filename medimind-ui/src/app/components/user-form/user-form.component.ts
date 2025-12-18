import { Component, EventEmitter, Output } from '@angular/core';

@Component({
  selector: 'app-user-form',
  templateUrl: './user-form.component.html',
  styleUrls: ['./user-form.component.css']
})
export class UserFormComponent {
  name = '';
  age!: number;
  gender = '';

  errorMessage = '';

  @Output() startChat = new EventEmitter<string>();

  // Name: letters and spaces only
  isValidName(name: string): boolean {
    return /^[A-Za-z ]+$/.test(name.trim());
  }

  submit() {
    this.errorMessage = '';

    // Name validation
    if (!this.name || !this.isValidName(this.name)) {
      this.errorMessage = 'Please enter a valid name (letters only)';
      return;
    }

    // Age validation: empty, negative, zero
    if (!this.age || this.age <= 0) {
      this.errorMessage = 'Please enter a valid age';
      return;
    }

    // 🔥 NEW AGE LIMIT RULE
    if (this.age >= 100) {
      this.errorMessage = 'Please enter a valid age below 100';
      return;
    }

    // Gender validation
    if (!this.gender) {
      this.errorMessage = 'Please select a gender';
      return;
    }

    // All validations passed
    this.startChat.emit(this.name.trim());
  }
}



