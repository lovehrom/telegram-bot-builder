export type BlockType =
  | 'start'
  | 'end'
  | 'text'
  | 'video'
  | 'image'
  | 'quiz'
  | 'decision'
  | 'menu'
  | 'confirmation'
  | 'course_menu'
  | 'payment_gate'
  | 'create_payment'
  | 'action'
  | 'input'
  | 'delay'
  | 'random';

export interface BaseConfig {
  [key: string]: any;
}

export interface TextBlockConfig extends BaseConfig {
  text: string;
  parse_mode?: 'HTML' | 'Markdown';
}

export interface VideoBlockConfig extends BaseConfig {
  video_file_id: string;
  caption?: string;
  protect_content?: boolean;
}

export interface ImageBlockConfig extends BaseConfig {
  photo_file_id: string;
  caption?: string;
  parse_mode?: 'HTML' | 'Markdown';
  protect_content?: boolean;
}

export interface DelayBlockConfig extends BaseConfig {
  duration: number;
  show_typing?: boolean;
}

export interface ConfirmationBlockConfig extends BaseConfig {
  text?: string;
  confirm_label?: string;
  cancel_label?: string;
}

export interface CourseMenuBlockConfig extends BaseConfig {
  text?: string;
  show_locked?: boolean;
  locked_message?: string;
}

export interface QuizBlockConfig extends BaseConfig {
  question: string;
  options: string[];
  correct_index: number;
  explanation?: string;
}

export interface DecisionBlockConfig extends BaseConfig {
  variable: string;
  operator: 'equals' | 'not_equals' | 'greater' | 'less' | 'contains';
  value: any;
}

export interface MenuBlockConfig extends BaseConfig {
  text: string;
  buttons: Array<{
    label: string;
    callback_data: string;
  }>;
}

export interface PaymentGateBlockConfig extends BaseConfig {
  required: boolean;
  unpaid_message: string;
}

export interface EndBlockConfig extends BaseConfig {
  final_message?: string;
}

export interface ActionBlockConfig extends BaseConfig {
  action_type: 'set_variable' | 'increment' | 'decrement';
  variable_name: string;
  variable_value?: any;
  increment_by?: number;
  decrement_by?: number;
}

export interface InputBlockConfig extends BaseConfig {
  prompt: string;
  variable_name: string;
  input_type?: 'text' | 'number' | 'email' | 'phone';
  validation_message?: string;
  parse_mode?: 'HTML' | 'Markdown';
}

export interface RandomBlockConfig extends BaseConfig {
  mode: 'equal' | 'weighted';
  branches?: string[];  // для mode='equal'
  weights?: Record<string, number>;  // для mode='weighted'
}

export type BlockConfig =
  | TextBlockConfig
  | VideoBlockConfig
  | ImageBlockConfig
  | DelayBlockConfig
  | ConfirmationBlockConfig
  | CourseMenuBlockConfig
  | QuizBlockConfig
  | DecisionBlockConfig
  | MenuBlockConfig
  | PaymentGateBlockConfig
  | EndBlockConfig
  | ActionBlockConfig
  | InputBlockConfig
  | RandomBlockConfig
  | BaseConfig;

export interface FlowBlock {
  id: number;
  flow_id: number;
  block_type: BlockType;
  label: string;
  config: BlockConfig;
  position_x?: number;
  position_y?: number;
  created_at: string;
  updated_at: string;
}

export interface FlowConnection {
  id: number;
  flow_id: number;
  from_block_id: number;
  to_block_id: number;
  condition: string | null;
  condition_config: Record<string, any>;
  connection_style: Record<string, any>;
}

export interface ConversationFlow {
  id: number;
  name: string;
  description?: string;
  is_active: boolean;
  start_block_id?: number;
  created_at: string;
  updated_at: string;
  blocks?: FlowBlock[];
  connections?: FlowConnection[];
}

export interface FlowNode {
  id: string;
  type: BlockType;
  position: { x: number; y: number };
  data: {
    id: number;
    label: string;
    config: BlockConfig;
    blockType: BlockType;
  };
}

export interface FlowEdge {
  id: string;
  source: string;
  target: string;
  sourceHandle?: string;
  targetHandle?: string;
  label?: string;
  type?: string;
  data?: {
    condition?: string;
  };
}

export interface FlowTemplate {
  id: number;
  name: string;
  description?: string;
  flow_id: number;
  blocks_data?: string; // JSON string
  connections_data?: string; // JSON string
  created_at: string;
}
