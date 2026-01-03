import { ComponentFixture, TestBed } from '@angular/core/testing';
import { NavbarComponent } from './navbar.component';
import { AuthService } from 'src/app/shared/auth.service';
import { ChatService } from 'src/app/shared/chat.service';
import { Router } from '@angular/router';
import { BehaviorSubject, of, throwError } from 'rxjs';
import { NO_ERRORS_SCHEMA } from '@angular/core';

describe('NavbarComponent', () => {
  let component: NavbarComponent;
  let fixture: ComponentFixture<NavbarComponent>;
  let authServiceSpy: jasmine.SpyObj<AuthService>;
  let chatServiceSpy: jasmine.SpyObj<ChatService>;
  let routerSpy: jasmine.SpyObj<Router>;

  beforeEach(async () => {
    // Mock AuthService
    const authSpy = jasmine.createSpyObj('AuthService', ['isLoggedIn', 'clearUser']);
    authSpy.userData$ = new BehaviorSubject<any>({ name: 'Test User', email: 'test@example.com' });

    // Mock ChatService
    const chatSpy = jasmine.createSpyObj('ChatService', [
      'toggleSidebar',
      'getSessionId',
      'resetChat',
      'clearSession'
    ]);

    // Default returns
    chatSpy.getSessionId.and.returnValue(null);
    chatSpy.resetChat.and.returnValue(of({ success: true }));

    // Mock Router
    const rSpy = jasmine.createSpyObj('Router', ['navigate']);

    await TestBed.configureTestingModule({
      declarations: [NavbarComponent],
      providers: [
        { provide: AuthService, useValue: authSpy },
        { provide: ChatService, useValue: chatSpy },
        { provide: Router, useValue: rSpy }
      ],
      schemas: [NO_ERRORS_SCHEMA]
    })
      .compileComponents();

    fixture = TestBed.createComponent(NavbarComponent);
    component = fixture.componentInstance;
    authServiceSpy = TestBed.inject(AuthService) as jasmine.SpyObj<AuthService>;
    chatServiceSpy = TestBed.inject(ChatService) as jasmine.SpyObj<ChatService>;
    routerSpy = TestBed.inject(Router) as jasmine.SpyObj<Router>;

    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });

  it('should display user first name', () => {
    expect(component.userName).toBe('Test');
  });

  it('should toggle menu', () => {
    expect(component.menuOpen).toBeFalse();
    component.toggleMenu();
    expect(component.menuOpen).toBeTrue();
    component.toggleMenu();
    expect(component.menuOpen).toBeFalse();
  });

  it('should toggle sidebar via chat service', () => {
    component.toggleSidebar();
    expect(chatServiceSpy.toggleSidebar).toHaveBeenCalled();
  });

  it('should start new chat (clear session) if no active session', () => {
    chatServiceSpy.getSessionId.and.returnValue(null);
    component.newChat();
    expect(chatServiceSpy.clearSession).toHaveBeenCalled();
    expect(component.menuOpen).toBeFalse();
  });

  it('should reset chat and then clear session if active session exists', () => {
    const sessionId = 'session-123';
    chatServiceSpy.getSessionId.and.returnValue(sessionId);
    chatServiceSpy.resetChat.and.returnValue(of({})); // Success

    component.newChat();

    expect(chatServiceSpy.resetChat).toHaveBeenCalledWith(sessionId);
    expect(chatServiceSpy.clearSession).toHaveBeenCalled();
  });

  it('should handle reset chat error gracefully', () => {
    const sessionId = 'session-error';
    chatServiceSpy.getSessionId.and.returnValue(sessionId);
    chatServiceSpy.resetChat.and.returnValue(throwError(() => ({ status: 500 })));

    component.newChat();

    expect(chatServiceSpy.resetChat).toHaveBeenCalled();
    // Should still clear session on error
    expect(chatServiceSpy.clearSession).toHaveBeenCalled();
  });

  it('should logout user', () => {
    component.logout();
    expect(authServiceSpy.clearUser).toHaveBeenCalled();
    expect(chatServiceSpy.clearSession).toHaveBeenCalled();
    expect(routerSpy.navigate).toHaveBeenCalledWith(['/login']);
    expect(component.menuOpen).toBeFalse();
  });
});
