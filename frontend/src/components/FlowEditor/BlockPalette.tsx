import { useState, useCallback, memo } from 'react';
import { Node } from 'reactflow';
import { MessageSquare, Video, HelpCircle, GitBranch, List, CreditCard, Play, Square, Image, Clock, CheckCircle, BookOpen, Zap, Shuffle, Edit3 } from 'lucide-react';
import type { BlockType } from '@/types/flow';
import { logger } from '@/utils/logger';

interface BlockPaletteProps {
  onAddNode: (node: Node) => void;
}

const blockTypes = [
  {
    type: 'start',
    label: 'Старт',
    icon: Play,
    color: 'bg-green-500',
    description: '👋 Старт. Сюда пользователь попадает в начале.',
    hint: 'Всегда один в flow. Автоматически переходит к следующему блоку.',
    complexity: 'easy'
  },
  {
    type: 'text',
    label: 'Текст',
    icon: MessageSquare,
    color: 'bg-blue-500',
    description: 'Отправить текстовое сообщение пользователю',
    hint: 'Поддерживает HTML форматирование: <b>жирный</b>, <i>курсив</i>',
    complexity: 'easy'
  },
  {
    type: 'video',
    label: 'Видео',
    icon: Video,
    color: 'bg-purple-500',
    description: 'Отправить видео пользователю',
    hint: 'Выберите видео из медиа библиотеки или введите File ID вручную.',
    complexity: 'medium'
  },
  {
    type: 'image',
    label: 'Изображение',
    icon: Image,
    color: 'bg-pink-400',
    description: 'Отправить фото пользователю',
    hint: 'Выберите фото из медиа библиотеки или введите File ID вручную.',
    complexity: 'easy'
  },
  {
    type: 'delay',
    label: 'Задержка',
    icon: Clock,
    color: 'bg-gray-500',
    description: 'Пауза перед следующим сообщением',
    hint: 'Автоматический переход после задержки. Можно показать "печатает...".',
    complexity: 'easy'
  },
  {
    type: 'confirmation',
    label: 'Подтверждение',
    icon: CheckCircle,
    color: 'bg-teal-500',
    description: 'Кнопки Да/Нет (например "Посмотрел?")',
    hint: 'Два выхода: conf_confirmed и conf_cancelled.',
    complexity: 'easy'
  },
  {
    type: 'course_menu',
    label: 'Меню курсов',
    icon: BookOpen,
    color: 'bg-amber-600',
    description: '📚 Меню с выбором курса',
    hint: 'Показывает все активные flow. Оплаченные курсы доступны.',
    complexity: 'hard'
  },
  {
    type: 'quiz',
    label: 'Викторина',
    icon: HelpCircle,
    color: 'bg-yellow-500',
    description: '❓ Вопрос с вариантами ответов',
    hint: 'Минимум 2 варианта ответа. Правильный ответ указывается индексом (нумерация с 0).',
    complexity: 'medium'
  },
  {
    type: 'decision',
    label: 'Условие',
    icon: GitBranch,
    color: 'bg-orange-500',
    description: '🔀 Проверка условия (Да/Нет)',
    hint: 'Доступные переменные: quiz_passed (bool), user.is_paid (bool), context.score (number).',
    complexity: 'hard'
  },
  {
    type: 'menu',
    label: 'Меню',
    icon: List,
    color: 'bg-indigo-500',
    description: 'Кнопки для навигации',
    hint: 'Каждая кнопка ведет к своему блоку. Callback_data должен быть уникальным.',
    complexity: 'medium'
  },
  {
    type: 'payment_gate',
    label: 'Проверка оплаты',
    icon: CreditCard,
    color: 'bg-pink-500',
    description: '💳 Проверяет оплату доступа',
    hint: 'Проверяет user.is_paid из базы данных. Имеет два выхода: paid и unpaid.',
    complexity: 'medium'
  },
  {
    type: 'create_payment',
    label: 'Создать платёж',
    icon: CreditCard,
    color: 'bg-rose-500',
    description: '💳 Создаёт платёжный инвойс',
    hint: 'Генерирует ссылку на оплату для пользователя.',
    complexity: 'medium'
  },
  {
    type: 'action',
    label: 'Действие',
    icon: Zap,
    color: 'bg-violet-600',
    description: '⚡ Выполнить действие с переменными',
    hint: 'Установка, увеличение или уменьшение переменных в context.',
    complexity: 'medium'
  },
  {
    type: 'input',
    label: 'Ввод данных',
    icon: Edit3,
    color: 'bg-cyan-500',
    description: '📝 Запросить ввод от пользователя',
    hint: 'Текст, число, email или телефон. Валидация и сохранение в переменную.',
    complexity: 'easy'
  },
  {
    type: 'random',
    label: 'Случайный выбор',
    icon: Shuffle,
    color: 'bg-amber-500',
    description: '🎲 Случайное ветвление',
    hint: 'Равновероятный или взвешенный выбор следующего блока.',
    complexity: 'medium'
  },
  {
    type: 'end',
    label: 'Конец',
    icon: Square,
    color: 'bg-red-500',
    description: 'Завершение flow',
    hint: 'Отправляет финальное сообщение пользователю и завершает диалог.',
    complexity: 'easy'
  },
];

function BlockPalette({ onAddNode }: BlockPaletteProps) {
  const [hoveredBlock, setHoveredBlock] = useState<typeof blockTypes[0] | null>(null);

  const handleAddBlock = useCallback((blockType: BlockType) => {
    const newNode: Node = {
      id: `${blockType}-${Date.now()}`,
      type: blockType,
      position: { x: Math.random() * 400 + 100, y: Math.random() * 300 + 100 },
      data: {
        id: `${blockType}-${Date.now()}`,
        label: blockTypes.find((bt) => bt.type === blockType)?.label || blockType,
        config: getDefaultConfig(blockType),
        blockType: blockType,
      },
    };
    logger.debug('Adding block:', newNode);
    onAddNode(newNode);
  }, [onAddNode]);

  const getComplexityIcon = useCallback((complexity: string) => {
    switch (complexity) {
      case 'easy':
        return '🟢';
      case 'medium':
        return '🟡';
      case 'hard':
        return '🔴';
      default:
        return '';
    }
  }, []);

  return (
    <div className="p-4">
      <h2 className="mb-1 text-lg font-semibold" style={{ color: '#FFFFFF' }}>🧩 Блоки</h2>
      <p className="mb-4 text-xs" style={{ color: '#71717A' }}>Перетащите на холст</p>
      <div className="space-y-2" role="list" aria-label="Список типов блоков">
        {blockTypes.map((block) => {
          const Icon = block.icon;
          return (
            <div
              key={block.type}
              className="relative"
              onMouseEnter={() => setHoveredBlock(block)}
              onMouseLeave={() => setHoveredBlock(null)}
            >
              <button
                onClick={() => handleAddBlock(block.type as BlockType)}
                className="flex w-full items-center gap-3 rounded-lg border p-3 transition-all duration-200"
                style={{ background: '#1A1A1A', borderColor: '#27272A' }}
                onMouseEnter={(e) => { e.currentTarget.style.background = '#222222'; e.currentTarget.style.borderColor = '#3B82F6'; }}
                onMouseLeave={(e) => { e.currentTarget.style.background = '#1A1A1A'; e.currentTarget.style.borderColor = '#27272A'; }}
                aria-label={`Добавить блок: ${block.label}`}
                aria-describedby={`hint-${block.type}`}
              >
                <div className={`${block.color} rounded-md p-2`} aria-hidden="true">
                  <Icon className="h-4 w-4 text-white" />
                </div>
                <div className="flex-1 text-left">
                  <div className="flex items-center gap-2">
                    <span className="font-medium" style={{ color: '#FFFFFF' }}>{block.label}</span>
                    <span className="text-xs" aria-hidden="true">{getComplexityIcon(block.complexity)}</span>
                  </div>
                </div>
                <span className="text-xs" style={{ color: '#71717A' }} aria-hidden="true">+</span>
              </button>

              {/* Tooltip — скрыт на мобильных для удобства */}
              {hoveredBlock === block && (
                <div
                  id={`hint-${block.type}`}
                  className="absolute left-full ml-2 top-0 z-50 w-64 rounded-lg border p-3 shadow-lg hidden md:block"
                  style={{ background: '#1A1A1A', borderColor: '#27272A' }}
                  role="tooltip"
                  aria-hidden="true"
                >
                  <p className="mb-2 text-sm font-medium" style={{ color: '#FFFFFF' }}>
                    {block.description}
                  </p>
                  <p className="text-xs" style={{ color: '#A1A1AA' }}>
                    💡 {block.hint}
                  </p>
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}

// Custom comparison function for BlockPalette
const arePropsEqual = (prevProps: BlockPaletteProps, nextProps: BlockPaletteProps) => {
  return prevProps.onAddNode === nextProps.onAddNode;
};

export const BlockPaletteMemo = memo(BlockPalette, arePropsEqual);
BlockPaletteMemo.displayName = 'BlockPalette';

// Export as both for backward compatibility
export { BlockPalette };
export default BlockPaletteMemo;

function getDefaultConfig(blockType: BlockType): Record<string, any> {
  switch (blockType) {
    case 'text':
      return { text: '', parse_mode: 'HTML' };
    case 'video':
      return { video_file_id: '', caption: '', protect_content: true };
    case 'image':
      return { photo_file_id: '', caption: '', parse_mode: 'HTML', protect_content: true };
    case 'delay':
      return { duration: 5, show_typing: true };
    case 'confirmation':
      return { text: 'Вы подтверждаете действие?', confirm_label: '✅ Да', cancel_label: '❌ Нет' };
    case 'course_menu':
      return { text: '📚 Выберите курс:', show_locked: true, locked_message: 'Этот курс требует оплаты' };
    case 'quiz':
      return { question: '', options: ['', '', '', ''], correct_index: 0 };
    case 'decision':
      return { variable: '', operator: 'equals', value: '' };
    case 'menu':
      return { text: '', buttons: [{ label: '', callback_data: '' }] };
    case 'payment_gate':
      return { required: true, unpaid_message: 'Для доступа требуется оплата.' };
    case 'create_payment':
      return { amount: 0, description: '' };
    case 'action':
      return { action_type: 'set_variable', variable_name: '', variable_value: '' };
    case 'input':
      return { prompt: 'Введите значение:', variable_name: 'user_input', input_type: 'text', validation_message: 'Неверный формат ввода' };
    case 'random':
      return { mode: 'equal', branches: ['branch_a', 'branch_b'] };
    case 'end':
      return { final_message: 'Сценарий завершён!' };
    default:
      return {};
  }
}
