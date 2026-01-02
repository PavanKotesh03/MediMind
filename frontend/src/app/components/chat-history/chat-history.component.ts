// import { Component, OnInit, OnDestroy, Output, EventEmitter } from '@angular/core';
// import { ChatService } from '../../shared/chat.service';
// import { AuthService } from '../../shared/auth.service';
// import { Subscription } from 'rxjs';

// interface SessionSummary {
//   session_id: string;
//   title: string;
//   status: string;
//   created_at: string;
//   message_count: number;
// }

// interface GroupedHistory {
//   today: SessionSummary[];
//   yesterday: SessionSummary[];
//   this_week: SessionSummary[];
//   this_month: SessionSummary[];
//   older: SessionSummary[];
// }

// @Component({
//   selector: 'app-chat-history',
//   templateUrl: './chat-history.component.html',
//   styleUrls: ['./chat-history.component.css']
// })
// export class ChatHistoryComponent implements OnInit, OnDestroy {
//   @Output() sessionSelected = new EventEmitter<string>();
//   @Output() newChatClicked = new EventEmitter<void>();

//   groupedHistory: GroupedHistory = {
//     today: [],
//     yesterday: [],
//     this_week: [],
//     this_month: [],
//     older: []
//   };

//   isLoading = false;
//   userEmail = '';
//   activeSessionId: string | null = null;

//   private subscriptions: Subscription[] = [];
//   private refreshInterval: any;

//   constructor(
//     private chatService: ChatService,
//     private authService: AuthService
//   ) {}

//   ngOnInit() {
//     // Get user email
//     const userSub = this.authService.userData$.subscribe(userData => {
//       if (userData) {
//         this.userEmail = userData.email;
//         this.loadHistory();
//       }
//     });
//     this.subscriptions.push(userSub);

//     // Reload every 5 minutes instead of 60 seconds
//     this.refreshInterval = setInterval(() => {
//       if (this.userEmail) {
//         console.log('Auto-refreshing history (5 min interval)');
//         this.loadHistory();
//       }
//     }, 300000); // 5 minutes (300,000ms)

//     // Reload history when chat resets
//     const resetSub = this.chatService.reset$.subscribe(reset => {
//       if (reset && this.userEmail) {
//         console.log('Reloading history after reset');
//         this.loadHistory();
//       }
//     });
//     this.subscriptions.push(resetSub);
//   }

//   ngOnDestroy() {
//     // Clean up subscriptions and interval
//     this.subscriptions.forEach(sub => sub.unsubscribe());
//     if (this.refreshInterval) {
//       clearInterval(this.refreshInterval);
//     }
//   }

//   loadHistory() {
//     if (!this.userEmail) return;

//     this.isLoading = true;
//     this.chatService.getGroupedHistory(this.userEmail).subscribe({
//       next: (response: any) => {
//         this.groupedHistory = response.data;
//         this.isLoading = false;
//         console.log('History loaded:', response.data);
//       },
//       error: (error) => {
//         console.error('Error loading history:', error);
//         this.isLoading = false;

//         // Show user-friendly error
//         if (error.status === 401) {
//           console.log('Token expired - user will be redirected to login');
//         }
//       }
//     });
//   }

//   // Manual refresh button
//   refreshHistory() {
//     if (!this.userEmail) return;

//     console.log('Manually refreshing history');
//     this.isLoading = true;
//     this.chatService.refreshHistory(this.userEmail).subscribe({
//       next: (response: any) => {
//         this.groupedHistory = response.data;
//         this.isLoading = false;
//         console.log('History refreshed');
//       },
//       error: (error) => {
//         console.error('Error refreshing history:', error);
//         this.isLoading = false;
//       }
//     });
//   }

//   selectSession(sessionId: string) {
//     this.activeSessionId = sessionId;
//     this.sessionSelected.emit(sessionId);
//   }

//   deleteSession(sessionId: string, event: Event) {
//     event.stopPropagation();

//     if (!confirm('Delete this conversation?')) return;

//     this.chatService.deleteConversation(sessionId, this.userEmail).subscribe({
//       next: () => {
//         console.log('Session deleted');
//         this.loadHistory(); // Reload after delete
//       },
//       error: (error) => {
//         console.error('Error deleting:', error);
//         alert('Failed to delete conversation');
//       }
//     });
//   }

//   formatDate(dateString: string): string {
//     const date = new Date(dateString);
//     const now = new Date();
//     const diffMs = now.getTime() - date.getTime();
//     const diffMins = Math.floor(diffMs / 60000);
//     const diffHours = Math.floor(diffMs / 3600000);

//     if (diffMins < 1) return 'Just now';
//     if (diffMins < 60) return `${diffMins}m ago`;
//     if (diffHours < 24) return `${diffHours}h ago`;
//     return date.toLocaleDateString();
//   }

//   hasHistory(): boolean {
//     return this.groupedHistory.today.length > 0 ||
//            this.groupedHistory.yesterday.length > 0 ||
//            this.groupedHistory.this_week.length > 0 ||
//            this.groupedHistory.this_month.length > 0 ||
//            this.groupedHistory.older.length > 0;
//   }
// }


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

  isLoading = false;
  activeSessionId: string | null = null;

  private subscriptions = new Subscription();
  private refreshIntervalId: number | null = null;

  constructor(private chatService: ChatService) { }

  ngOnInit() {
    this.loadHistory();

    // Auto refresh every 5 minutes
    this.refreshIntervalId = window.setInterval(() => {
      this.loadHistory();
    }, 300000);

    // React only to TRUE reset events
    this.subscriptions.add(
      this.chatService.reset$.subscribe(reset => {
        if (reset === true) {
          this.loadHistory();
        }
      })
    );
  }

  ngOnDestroy() {
    this.subscriptions.unsubscribe();
    if (this.refreshIntervalId !== null) {
      clearInterval(this.refreshIntervalId);
    }
  }

  loadHistory() {
    this.isLoading = true;

    this.chatService.getGroupedHistory().subscribe({
      next: (response: any) => {
        if (response?.success && response?.data) {
          this.groupedHistory = response.data;
        }
        this.isLoading = false;
      },
      error: (error) => {
        console.error('Error loading history:', error);
        this.isLoading = false;
      }
    });
  }

  refreshHistory() {
    this.loadHistory();
  }


  selectSession(sessionId: string) {
    this.activeSessionId = sessionId;
    this.sessionSelected.emit(sessionId);
  }

  deleteSession(sessionId: string, event: Event) {
    event.stopPropagation();
    if (!confirm('Delete this conversation?')) return;

    this.chatService.deleteConversation(sessionId).subscribe({
      next: () => this.loadHistory(),
      error: () => alert('Failed to delete conversation')
    });
  }

  hasHistory(): boolean {
    return Object.values(this.groupedHistory).some(list => list.length > 0);
  }

  // REQUIRED BY TEMPLATE
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

  // OPTIONAL (performance)
  trackBySession(_: number, session: SessionSummary) {
    return session.session_id;
  }
}
