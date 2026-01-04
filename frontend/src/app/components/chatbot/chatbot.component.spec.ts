import { ComponentFixture, TestBed, fakeAsync, tick } from '@angular/core/testing';
import { ChatbotComponent } from './chatbot.component';
import { ChatService } from 'src/app/shared/chat.service';
import { ActivatedRoute, Router } from '@angular/router';
import { of, throwError, BehaviorSubject } from 'rxjs';
import { NO_ERRORS_SCHEMA } from '@angular/core';

describe('ChatbotComponent', () => {
  let component: ChatbotComponent;
  let fixture: ComponentFixture<ChatbotComponent>;
  let chatServiceSpy: jasmine.SpyObj<ChatService>;
  let routerSpy: jasmine.SpyObj<Router>;
  let routeStub: any;

  beforeEach(async () => {
    // Mock ChatService
    const chatServiceMock = jasmine.createSpyObj('ChatService', [
      'getConversation',
      'sendMessage',
      'startInterview',
      'setSessionId',
      'getSessionId',
      'clearSession',
      'toggleSidebar'
    ]);

    // Add Observable properties
    chatServiceMock.sidebarOpen$ = new BehaviorSubject<boolean>(false);
    chatServiceMock.reset$ = new BehaviorSubject<boolean>(false);
    chatServiceMock.sessionId$ = new BehaviorSubject<string | null>(null);

    // Default returns
    chatServiceMock.getConversation.and.returnValue(of({ data: { messages: [], status: 'in_progress' } }));
    chatServiceMock.sendMessage.and.returnValue(of({ data: { reply: 'Test Reply' } }));
    chatServiceMock.startInterview.and.returnValue(of({ data: { session_id: 'new-session-id' } }));
    chatServiceMock.getSessionId.and.returnValue(null);

    // Mock Router
    routerSpy = jasmine.createSpyObj('Router', ['navigate']);

    // Mock ActivatedRoute
    routeStub = {
      params: new BehaviorSubject<any>({})
    };

    await TestBed.configureTestingModule({
      declarations: [ChatbotComponent],
      providers: [
        { provide: ChatService, useValue: chatServiceMock },
        { provide: Router, useValue: routerSpy },
        { provide: ActivatedRoute, useValue: routeStub }
      ],
      schemas: [NO_ERRORS_SCHEMA]
    }).compileComponents();

    fixture = TestBed.createComponent(ChatbotComponent);
    component = fixture.componentInstance;
    chatServiceSpy = TestBed.inject(ChatService) as jasmine.SpyObj<ChatService>;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
    expect(component.messages.length).toBeGreaterThan(0); // Should have initial greeting
    expect(component.messages[0].role).toBe('assistant');
  });

  it('should initialize with session ID from URL', () => {
    const sessionId = 'test-session-123';
    // Simulate URL param change
    routeStub.params.next({ sessionId: sessionId });

    expect(chatServiceSpy.setSessionId).toHaveBeenCalledWith(sessionId);
    expect(chatServiceSpy.getConversation).toHaveBeenCalledWith(sessionId);
    expect(component.sessionId).toBe(sessionId);
  });

  it('should send a message and handle response', fakeAsync(() => {
    component.input = 'Hello';
    chatServiceSpy.startInterview.and.returnValue(of({
      data: {
        session_id: 'new-session',
        reply: 'Hi there'
      }
    }));

    component.send();

    expect(component.messages.some(m => m.content === 'Hello')).toBeTrue();
    expect(chatServiceSpy.startInterview).toHaveBeenCalled();

    // Advance time to allow typewriter effect to complete
    tick(1000); // Wait enough time for the typing to finish

    // After response
    expect(component.messages.some(m => m.content === 'Hi there')).toBeTrue();
    expect(component.isLoading).toBeFalse();
  }));

  it('should not send empty message', () => {
    chatServiceSpy.sendMessage.calls.reset();
    chatServiceSpy.startInterview.calls.reset();

    component.input = '   ';
    component.send();
    expect(chatServiceSpy.sendMessage).not.toHaveBeenCalled();
    expect(chatServiceSpy.startInterview).not.toHaveBeenCalled();
  });

  it('should handle conversation completion', () => {
    component.input = 'Finish';
    component.sessionId = 'existing-session';

    chatServiceSpy.sendMessage.and.returnValue(of({
      data: {
        finished: true,
        final: {
          disease: 'Flu',
          severity: 'Moderate',
          reason: 'Symptoms match',
          explanation: 'Rest well'
        }
      }
    }));

    component.send();

    expect(component.conversationFinished).toBeTrue();
    const lastMsg = component.messages[component.messages.length - 1];
    expect(lastMsg.isFinal).toBeTrue();
    expect(lastMsg.content).toContain('Assessment Complete');
  });

  it('should reset chat when reset event received', () => {
    // Simulate reset event
    (chatServiceSpy.reset$ as BehaviorSubject<boolean>).next(true);

    expect(component.messages.length).toBe(1); // Reset to greeting
    expect(component.sessionId).toBeNull();
    expect(chatServiceSpy.startInterview).toHaveBeenCalled();
  });
});
