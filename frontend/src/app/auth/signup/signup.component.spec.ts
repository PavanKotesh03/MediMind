import { ComponentFixture, TestBed } from '@angular/core/testing';
import { SignupComponent } from './signup.component';
import { AuthService } from '../../shared/auth.service';
import { Router } from '@angular/router';
import { of, throwError } from 'rxjs';
import { FormsModule, NgForm } from '@angular/forms';
import { NO_ERRORS_SCHEMA } from '@angular/core';

describe('SignupComponent', () => {
  let component: SignupComponent;
  let fixture: ComponentFixture<SignupComponent>;
  let authServiceSpy: jasmine.SpyObj<AuthService>;
  let routerSpy: jasmine.SpyObj<Router>;

  beforeEach(async () => {
    const authSpy = jasmine.createSpyObj('AuthService', ['register']);
    const rSpy = jasmine.createSpyObj('Router', ['navigate']);

    await TestBed.configureTestingModule({
      declarations: [SignupComponent],
      imports: [FormsModule],
      providers: [
        { provide: AuthService, useValue: authSpy },
        { provide: Router, useValue: rSpy }
      ],
      schemas: [NO_ERRORS_SCHEMA]
    })
      .compileComponents();

    fixture = TestBed.createComponent(SignupComponent);
    component = fixture.componentInstance;
    authServiceSpy = TestBed.inject(AuthService) as jasmine.SpyObj<AuthService>;
    routerSpy = TestBed.inject(Router) as jasmine.SpyObj<Router>;

    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });

  it('should stop submission if passwords mismtach', () => {
    component.password = '123';
    component.confirmPassword = '456';

    // Create a mock form
    const form = {
      invalid: false,
      controls: { confirmPassword: { markAsTouched: () => { } } }
    } as any;

    component.signup(form);

    expect(authServiceSpy.register).not.toHaveBeenCalled();
    // We expect some side effect like markAsTouched, but primarily verifying register isn't called
  });

  it('should register successfully with valid data', () => {
    component.email = 'new@example.com';
    component.password = 'pass';
    component.confirmPassword = 'pass';
    component.firstName = 'John';
    component.lastName = 'Doe';
    component.age = 25;
    component.gender = 'Male';

    authServiceSpy.register.and.returnValue(of({ success: true, data: {} }));

    const form = {
      invalid: false,
      controls: {}
    } as any;

    component.signup(form);

    expect(authServiceSpy.register).toHaveBeenCalledWith('new@example.com', 'pass', 'John', 'Doe', 25, 'Male');
    expect(routerSpy.navigate).toHaveBeenCalledWith(['/chat']);
  });

  it('should handle registration error', () => {
    component.email = 'exist@example.com';
    component.password = 'pass';
    component.confirmPassword = 'pass';

    const form = { invalid: false, controls: {} } as any;

    authServiceSpy.register.and.returnValue(throwError(() => ({
      status: 400,
      error: { detail: 'Email already registered' }
    })));

    component.signup(form);

    expect(component.errors.general).toContain('already registered');
    expect(routerSpy.navigate).not.toHaveBeenCalled();
  });
});
