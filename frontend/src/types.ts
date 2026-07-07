export type User = {
  id: string; name: string; email: string; role_id: string; department_id: string | null;
  is_active: boolean; notifications_enabled: boolean; created_at: string;
  role_name: string | null; permission_keys: string[];
}

export type Attachment = { id: string; original_name: string; content_type: string; size_bytes: number }

export type Announcement = {
  id: string; title: string; content: string; is_global: boolean; is_pinned: boolean;
  requires_acknowledgement: boolean; comments_enabled: boolean; sender_id: string;
  publish_at: string; expires_at: string | null; created_at: string; attachments: Attachment[];
}

export type EventItem = {
  id: string; title: string; description: string | null; creator_id: string; start_time: string;
  end_time: string; location_type: 'ONLINE' | 'PHYSICAL' | 'HYBRID'; physical_location: string | null;
  meeting_link: string | null; is_global: boolean; announcement_id: string | null;
  created_at: string; attachments: Attachment[];
}

export type NotificationItem = {
  id: string; kind: string; title: string; body: string; payload: Record<string, string>;
  is_read: boolean; delivered_at: string | null; created_at: string;
}

export type Role = { id: string; name: string; description: string | null; permission_keys: string[] }
export type Department = { id: string; name: string; parent_id: string | null }
export type CommentItem = { id: string; announcement_id: string; user_id: string; user_name: string; content: string; created_at: string }
export type AudienceDirectory = {
  users: { id: string; name: string }[];
  roles: { id: string; name: string }[];
  departments: { id: string; name: string }[];
}
