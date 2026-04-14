import Joyride, { CallBackProps, STATUS, Step } from 'react-joyride';
import { Info } from 'lucide-react';

interface TourProps {
  run: boolean;
  onComplete: () => void;
  onSkip: () => void;
}

const tourSteps: Step[] = [
  {
    target: '.flow-editor-container',
    content: (
      <div className="space-y-3">
        <h3 className="text-lg font-semibold">👋 Добро пожаловать в Flow Editor!</h3>
        <p className="text-sm">
          Это визуальный редактор для создания диалоговых сценариев вашего Telegram бота.
          Давайте разберёмся, как это работает!
        </p>
      </div>
    ),
    placement: 'center',
    disableBeacon: true,
  },
  {
    target: '.block-palette',
    content: (
      <div className="space-y-3">
        <h3 className="text-lg font-semibold">🧩 Палитра блоков</h3>
        <p className="text-sm">
          Здесь находятся все доступные блоки для создания сценария. Нажмите на любой блок чтобы добавить его на холст.
        </p>
        <div className="rounded-lg bg-blue-50 p-3 dark:bg-blue-900/20">
          <p className="mb-2 text-xs font-semibold text-blue-900 dark:text-blue-300">
            💡 Совет:
          </p>
          <ul className="text-xs text-blue-800 dark:text-blue-400 space-y-1">
            <li>🟢 <strong>Зелёные</strong> — простые блоки (Старт, Текст)</li>
            <li>🟡 <strong>Жёлтые</strong> — средней сложности (Викторина, Меню)</li>
            <li>🔴 <strong>Красные</strong> — сложные блоки (Условие, Меню курсов)</li>
          </ul>
        </div>
      </div>
    ),
    placement: 'right',
  },
  {
    target: '.react-flow',
    content: (
      <div className="space-y-3">
        <h3 className="text-lg font-semibold">🎨 Холст для создания</h3>
        <p className="text-sm">
          Это ваша рабочая область. Перетащите блоки из палитры сюда и соединяйте их линиями для создания сценария.
        </p>
        <div className="space-y-2">
          <p className="text-xs font-semibold">Как работать:</p>
          <ul className="text-xs space-y-1">
            <li>• <strong>Добавить блок:</strong> нажмите на блок в палитре слева</li>
            <li>• <strong>Переместить:</strong> перетащите блок мышкой</li>
            <li>• <strong>Соединить:</strong> потяните от точки справа одного блока к точке слева другого</li>
            <li>• <strong>Редактировать:</strong> кликните на блок</li>
          </ul>
        </div>
      </div>
    ),
    placement: 'bottom',
  },
  {
    target: '.properties-panel',
    content: (
      <div className="space-y-3">
        <h3 className="text-lg font-semibold">⚙️ Панель свойств</h3>
        <p className="text-sm">
          Здесь вы можете редактировать выбранный блок: менять текст, добавлять изображения, настраивать кнопки и многое другое.
        </p>
        <div className="rounded-lg bg-purple-50 p-3 dark:bg-purple-900/20">
          <p className="text-xs text-purple-900 dark:text-purple-300">
            💡 Каждый тип блока имеет свои уникальные настройки!
          </p>
        </div>
      </div>
    ),
    placement: 'left',
  },
  {
    target: '.react-flow__minimap',
    content: (
      <div className="space-y-3">
        <h3 className="text-lg font-semibold">🗺️ Мини-карта</h3>
        <p className="text-sm">
          Для больших сценариий используйте мини-карту для навигации. Нажмите на неё чтобы переместиться к нужному месту.
        </p>
      </div>
    ),
    placement: 'left',
  },
  {
    target: '.save-button',
    content: (
      <div className="space-y-3">
        <h3 className="text-lg font-semibold">💾 Сохранение</h3>
        <p className="text-sm">
          Не забывайте сохранять изменения! Нажмите кнопку "Сохранить" чтобы применить все изменения.
        </p>
        <div className="rounded-lg bg-yellow-50 p-3 dark:bg-yellow-900/20">
          <p className="text-xs text-yellow-900 dark:text-yellow-300">
            ⚠️ Несохранённые изменения будут потеряны при закрытии страницы!
          </p>
        </div>
      </div>
    ),
    placement: 'bottom',
  },
  {
    target: '.practice-task',
    content: (
      <div className="space-y-3">
        <h3 className="text-lg font-semibold">🎯 Практика!</h3>
        <p className="text-sm">
          Попробуйте создать простой сценарий:
        </p>
        <ol className="text-xs space-y-2 list-decimal list-inside">
          <li>Добавьте блок <strong>Старт</strong></li>
          <li>Добавьте блок <strong>Текст</strong> и напишите приветствие</li>
          <li>Добавьте блок <strong>Конец</strong></li>
          <li>Соедините их: Старт → Текст → Конец</li>
          <li>Нажмите <strong>Сохранить</strong></li>
        </ol>
        <div className="mt-3 rounded-lg bg-green-50 p-3 dark:bg-green-900/20">
          <p className="text-xs text-green-900 dark:text-green-300">
            🎉 Отлично! Теперь вы готовы создавать свои сценарии!
          </p>
        </div>
      </div>
    ),
    placement: 'center',
  },
];

export function FlowEditorTour({ run, onComplete, onSkip }: TourProps) {
  const handleJoyrideCallback = (data: CallBackProps) => {
    const { status } = data;

    if (status === STATUS.FINISHED || status === STATUS.SKIPPED) {
      if (status === STATUS.FINISHED) {
        onComplete();
      } else {
        onSkip();
      }
    }
  };

  return (
    <>
      <Joyride
        steps={tourSteps}
        run={run}
        continuous
        showSkipButton
        showProgress
        disableOverlayClose
        locale={{
          back: 'Назад',
          close: 'Закрыть',
          last: 'Завершить',
          next: 'Далее',
          open: 'Открыть',
          skip: 'Пропустить',
        }}
        styles={{
          options: {
            primaryColor: '#3b82f6',
            zIndex: 10000,
          },
          tooltip: {
            borderRadius: '0.5rem',
            padding: '1rem',
            maxWidth: '400px',
          },
          tooltipContainer: {
            textAlign: 'left',
          },
          buttonNext: {
            backgroundColor: '#3b82f6',
            borderRadius: '0.375rem',
            padding: '0.5rem 1rem',
          },
          buttonBack: {
            color: '#6b7280',
            marginRight: '0.5rem',
          },
          buttonSkip: {
            color: '#9ca3af',
          },
        }}
        callback={handleJoyrideCallback}
      />
      {/* Custom tooltip icon */}
      <div className="fixed bottom-4 right-4 z-50 rounded-full bg-blue-500 p-3 text-white shadow-lg animate-bounce">
        <Info className="h-6 w-6" />
      </div>
    </>
  );
}
