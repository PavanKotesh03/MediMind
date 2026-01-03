import { ComponentFixture, TestBed, fakeAsync, tick, discardPeriodicTasks } from '@angular/core/testing';
import { ChatHistoryComponent } from './chat-history.component';
import { ChatService } from 'src/app/shared/chat.service';
import { BehaviorSubject, of, throwError } from 'rxjs';
import { NO_ERRORS_SCHEMA } from '@angular/core';

describe('ChatHistoryComponent', () => {
  let component: ChatHistoryComponent;
  let fixture: ComponentFixture<ChatHistoryComponent>;
  let chatServiceSpy: jasmine.SpyObj<ChatService>;

  const mockHistory = {
    today: [{ session_id: '1', title: 'Test 1', status: 'completed', created_at: new Date().toISOString(), message_count: 5 }],
    yesterday: [],
    this_week: [],
    this_month: [],
    older: []
  };

  beforeEach(async () => {
    const spy = jasmine.createSpyObj('ChatService', ['getGroupedHistory', 'deleteConversation']);
    spy.reset$ = new BehaviorSubject<boolean>(false);
    spy.getGroupedHistory.and.returnValue(of({ success: true, data: mockHistory }));

    await TestBed.configureTestingModule({
      declarations: [ChatHistoryComponent],
      providers: [
        { provide: ChatService, useValue: spy }
      ],
      schemas: [NO_ERRORS_SCHEMA]
    })
      .compileComponents();

    fixture = TestBed.createComponent(ChatHistoryComponent);
    component = fixture.componentInstance;
    chatServiceSpy = TestBed.inject(ChatService) as jasmine.SpyObj<ChatService>;
    // fixture.detectChanges(); // Moved to individual tests to support fakeAsync
  });

  it('should create', () => {
    fixture.detectChanges();
    expect(component).toBeTruthy();
  });

  it('should load history on init', () => {
    fixture.detectChanges();
    expect(chatServiceSpy.getGroupedHistory).toHaveBeenCalled();
    expect(component.groupedHistory).toEqual(mockHistory);
    expect(component.hasHistory()).toBeTrue();
  });

  it('should reload history when reset$ emits true', () => {
    fixture.detectChanges();
    chatServiceSpy.getGroupedHistory.calls.reset();
    (chatServiceSpy.reset$ as BehaviorSubject<boolean>).next(true); // Emit true
    expect(chatServiceSpy.getGroupedHistory).toHaveBeenCalled();
  });

  it('should NOT reload history when reset$ emits false', () => {
    fixture.detectChanges();
    chatServiceSpy.getGroupedHistory.calls.reset();
    (chatServiceSpy.reset$ as BehaviorSubject<boolean>).next(false); // Emit false (default)
    expect(chatServiceSpy.getGroupedHistory).not.toHaveBeenCalled();
  });

  it('should refresh history manually', () => {
    fixture.detectChanges();
    chatServiceSpy.getGroupedHistory.calls.reset();
    component.refreshHistory();
    expect(chatServiceSpy.getGroupedHistory).toHaveBeenCalled();
  });

  it('should select a session', () => {
    fixture.detectChanges();
    spyOn(component.sessionSelected, 'emit');
    component.selectSession('123');
    expect(component.activeSessionId).toBe('123');
    expect(component.sessionSelected.emit).toHaveBeenCalledWith('123');
  });

  it('should delete a session when confirmed', () => {
    fixture.detectChanges();
    spyOn(window, 'confirm').and.returnValue(true);
    chatServiceSpy.deleteConversation.and.returnValue(of({}));
    const event = new MouseEvent('click');

    component.deleteSession('1', event);

    expect(chatServiceSpy.deleteConversation).toHaveBeenCalledWith('1');
    expect(chatServiceSpy.getGroupedHistory).toHaveBeenCalled(); // Should reload
  });

  it('should NOT delete session when cancelled', () => {
    fixture.detectChanges();
    spyOn(window, 'confirm').and.returnValue(false);
    const event = new MouseEvent('click');

    component.deleteSession('1', event);

    expect(chatServiceSpy.deleteConversation).not.toHaveBeenCalled();
  });

  it('should format dates correctly', () => {
    // No detectChanges needed for pure method, but harmless
    const now = new Date();
    expect(component.formatDate(now.toISOString())).toBe('Just now');

    const twoMinsAgo = new Date(now.getTime() - 2 * 60000);
    expect(component.formatDate(twoMinsAgo.toISOString())).toBe('2m ago');

    const yesterday = new Date(now.getTime() - 25 * 3600000); // 25 hours ago
    expect(component.formatDate(yesterday.toISOString())).not.toContain('ago');
  });

  it('should handle auto-refresh interval', fakeAsync(() => {
    fixture.detectChanges(); // Starts interval in fakeAsync zone
    chatServiceSpy.getGroupedHistory.calls.reset();
    tick(300000); // 5 minutes
    expect(chatServiceSpy.getGroupedHistory).toHaveBeenCalled();
    discardPeriodicTasks();
  }));
});
