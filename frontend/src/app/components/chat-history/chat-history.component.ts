import { Component, OnInit, Output, EventEmitter } from '@angular/core';
import { ChatService } from '../../shared/chat.service';
import { AuthService } from '../../shared/auth.service';

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
export class ChatHistoryComponent implements OnInit {
  @Output() sessionSelected = new EventEmitter<string>();
  @Output() newChatClicked = new EventEmitter<void>();

  groupedHistory: GroupedHistory = {
    today: [],
    yesterday: [],
    this_week: [],
    this_month: [],
    older: []
  };

  isLoading = false;
  userEmail = '';
  activeSessionId: string | null = null;

  constructor(
    private chatService: ChatService,
    private authService: AuthService
  ) {}

  ngOnInit() {
    // Get user email
    this.authService.userData$.subscribe(userData => {
      if (userData) {
        this.userEmail = userData.email;
        this.loadHistory();
      }
    });

    // Reload history every 30 seconds
    setInterval(() => {
      if (this.userEmail) {
        this.loadHistory();
      }
    }, 30000);
  }

  loadHistory() {
    if (!this.userEmail) return;

    this.isLoading = true;
    this.chatService.getGroupedHistory(this.userEmail).subscribe({
      next: (history) => {
        this.groupedHistory = history;
        this.isLoading = false;
      },
      error: (error) => {
        console.error('Error loading history:', error);
        this.isLoading = false;
      }
    });
  }

  selectSession(sessionId: string) {
    this.activeSessionId = sessionId;
    this.sessionSelected.emit(sessionId);
  }

  deleteSession(sessionId: string, event: Event) {
    event.stopPropagation();
    
    if (!confirm('Delete this conversation?')) return;

    this.chatService.deleteConversation(sessionId, this.userEmail).subscribe({
      next: () => {
        this.loadHistory();
      },
      error: (error) => {
        console.error('Error deleting:', error);
      }
    });
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
}
