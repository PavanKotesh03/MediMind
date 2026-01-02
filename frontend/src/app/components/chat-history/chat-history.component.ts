import { Component, OnInit, OnDestroy, Output, EventEmitter } from '@angular/core';
import { ChatService } from '../../shared/chat.service';
import { Subscription } from 'rxjs';

interface SessionSummary {
  session_id: string;
  title: string;
  status: string;
  created_at: string;
  message_count: number;
}

interface GroupedHistory {
  today: SessionSummary[];
  yesterday: SessionSummary[];
  this_week: SessionSummary[];
  this_month: SessionSummary[];
  older: SessionSummary[];
}

@Component({
  selector: 'app-chat-history',
  templateUrl: './chat-history.component.html',
  styleUrls: ['./chat-history.component.css']
})
export class ChatHistoryComponent implements OnInit, OnDestroy {
  @Output() sessionSelected = new EventEmitter<string>();
  @Output() newChatClicked = new EventEmitter<void>();

  groupedHistory: GroupedHistory = {
    today: [],
    yesterday: [],
    this_week: [],
    this_month: [],
    older: []
  };

  loading: boolean = false;
  selectedSessionId: string | null = null;
  
  private isLoadingHistory = false;
  private subscriptions = new Subscription();
  private refreshIntervalId: any = null;

  constructor(private chatService: ChatService) {}

  ngOnInit() {
    this.loadHistory();

    // DISABLED AUTO-REFRESH - Only manual refresh now
    // Auto-refresh causes page reloads during conversations
    // this.refreshIntervalId = setInterval(() => {
    //   console.log('Auto-refreshing history');
    //   this.loadHistory();
    // }, 300000); // 5 minutes
  }

  ngOnDestroy() {
    this.subscriptions.unsubscribe();
    if (this.refreshIntervalId) {
      clearInterval(this.refreshIntervalId);
    }
  }

  loadHistory() {
    // Prevent multiple simultaneous calls
    if (this.isLoadingHistory) {
      console.log('History already loading, skipping...');
      return;
    }

    this.isLoadingHistory = true;
    this.loading = true;

    this.chatService.getGroupedHistory().subscribe({
      next: (response: any) => {
        this.groupedHistory = response.data || {
          today: [],
          yesterday: [],
          this_week: [],
          this_month: [],
          older: []
        };
        this.loading = false;
        this.isLoadingHistory = false;
      },
      error: (error) => {
        console.error('Error loading history:', error);
        this.loading = false;
        this.isLoadingHistory = false;
      }
    });
  }

  refreshHistory() {
    console.log('Manual refresh triggered');
    this.isLoadingHistory = false; // Reset flag
    this.loadHistory();
  }

  selectSession(sessionId: string) {
    this.selectedSessionId = sessionId;
    this.sessionSelected.emit(sessionId);
  }

  onNewChat() {
    this.selectedSessionId = null;
    this.newChatClicked.emit();
    console.log('HISTORY: New chat button clicked');
  }

  deleteChat(sessionId: string, event: Event) {
    event.stopPropagation();
    if (confirm('Are you sure you want to delete this conversation?')) {
      this.chatService.deleteConversation(sessionId).subscribe({
        next: () => {
          console.log('Conversation deleted');
          this.isLoadingHistory = false; // Reset flag before reload
          this.loadHistory();
          if (this.selectedSessionId === sessionId) {
            this.selectedSessionId = null;
            this.newChatClicked.emit();
          }
        },
        error: (error) => {
          console.error('Error deleting chat:', error);
          alert('Failed to delete conversation');
        }
      });
    }
  }

  formatDate(dateString: string): string {
    const date = new Date(dateString);
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffMins = Math.floor(diffMs / 60000);
    const diffHours = Math.floor(diffMs / 3600000);

    if (diffMins < 1) return 'Just now';
    if (diffMins < 60) return `${diffMins}m ago`;
    if (diffHours < 24) return `${diffHours}h ago`;
    return date.toLocaleDateString();
  }

  hasHistory(): boolean {
    return this.groupedHistory.today.length > 0 ||
           this.groupedHistory.yesterday.length > 0 ||
           this.groupedHistory.this_week.length > 0 ||
           this.groupedHistory.this_month.length > 0 ||
           this.groupedHistory.older.length > 0;
  }

  trackBySession(index: number, session: SessionSummary): string {
    return session.session_id;
  }
}
