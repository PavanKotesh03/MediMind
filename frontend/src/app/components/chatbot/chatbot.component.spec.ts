import { ComponentFixture, TestBed, fakeAsync, tick } from '@angular/core/testing';
import { ChatbotComponent } from './chatbot.component';
import { ChatService } from 'src/app/shared/chat.service';
import { ActivatedRoute, Router } from '@angular/router';
import { of, BehaviorSubject } from 'rxjs';
import { NO_ERRORS_SCHEMA } from '@angular/core';

describe('ChatbotComponent', () => {
  let component: ChatbotComponent;
  let fixture: ComponentFixture<ChatbotComponent>;
  let chatServiceSpy: jasmine.SpyObj<ChatService>;
  let routerSpy: jasmine.SpyObj<Router>;
  let routeStub: any;

  beforeEach(async () => {
    // Mock ChatService with new streaming methods
    const chatServiceMock = jasmine.createSpyObj('ChatService', [
      'getConversation',
      'sendMessage',
      'startChat',
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

  it('should send a message and handle streaming response (New Session)', fakeAsync(() => {
    component.input = 'Hello';
    component.sessionId = null; // New session

    // Mock startChat to simulate streaming
    chatServiceSpy.startChat.and.callFake((msg, onToken, onSessionId, onComplete, onError) => {
      // Simulate async behavior
      setTimeout(() => {
        onToken('Hi');
        onToken(' there');
        onSessionId('new-session-id');
        onComplete(false);
      }, 100);
    });

    component.send();

    expect(component.messages.some(m => m.content === 'Hello')).toBeTrue();
    expect(chatServiceSpy.startChat).toHaveBeenCalled();

    // Advance time to allow streaming to complete
    tick(100);

    // After response
    expect(component.messages.some(m => m.content === 'Hi there')).toBeTrue();
    expect(component.isLoading).toBeFalse();
    expect(component.isWaitingForResponse).toBeFalse();
    expect(component.sessionId as any).toBe('new-session-id');
  }));

  it('should send a message and handle streaming response (Existing Session)', fakeAsync(() => {
    component.input = 'How are you?';
    component.sessionId = 'existing-session';

    // Mock sendMessage to simulate streaming
    chatServiceSpy.sendMessage.and.callFake((sessId, msg, onToken, onFinal, onComplete, onError) => {
      setTimeout(() => {
        onToken('I am');
        onToken(' fine');
        onComplete(false);
      }, 100);
    });

    component.send();

    expect(component.messages.some(m => m.content === 'How are you?')).toBeTrue();
    expect(chatServiceSpy.sendMessage).toHaveBeenCalled();

    // Advance time
    tick(100);

    // After response
    expect(component.messages.some(m => m.content === 'I am fine')).toBeTrue();
    expect(component.isWaitingForResponse).toBeFalse();
  }));

  it('should not send empty message', () => {
    chatServiceSpy.sendMessage.calls.reset();
    chatServiceSpy.startChat.calls.reset();

    component.input = '   ';
    component.send();
    expect(chatServiceSpy.sendMessage).not.toHaveBeenCalled();
    expect(chatServiceSpy.startChat).not.toHaveBeenCalled();
  });

  it('should handle conversation completion', fakeAsync(() => {
    component.input = 'Finish';
    component.sessionId = 'existing-session';

    const finalData = {
      disease: 'Flu',
      severity: 'Moderate',
      reason: 'Symptoms match',
      explanation: 'Rest well'
    };

    chatServiceSpy.sendMessage.and.callFake((sessId, msg, onToken, onFinal, onComplete, onError) => {
      setTimeout(() => {
        onFinal(finalData);
        onComplete(true);
      }, 100);
    });

    component.send();
    tick(100);

    expect(component.conversationFinished).toBeTrue();
    const lastMsg = component.messages[component.messages.length - 1];
    expect(lastMsg.isFinal).toBeTrue();
    expect(lastMsg.content).toContain('Assessment Complete');
  }));

  it('should reset chat when reset event received', () => {
    // Simulate reset event
    (chatServiceSpy.reset$ as BehaviorSubject<boolean>).next(true);

    // Mock startChat for the auto-initialization after reset
    expect(chatServiceSpy.startChat).toHaveBeenCalled();
    expect(component.messages.length).toBe(1); // Reset to greeting
    expect(component.sessionId).toBeNull();
  });
});
