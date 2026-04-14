import { useEffect, useRef } from 'react';

export interface UseTouchGesturesOptions {
  onPinch?: (scale: number, centerX: number, centerY: number) => void;
  onPan?: (deltaX: number, deltaY: number) => void;
  onTap?: (x: number, y: number) => void;
  onDoubleTap?: (x: number, y: number) => void;
  isEnabled?: boolean;
  targetRef?: React.RefObject<HTMLElement>;
}

export interface TouchPoint {
  x: number;
  y: number;
  identifier: number;
}

export function useTouchGestures({
  onPinch,
  onPan,
  onTap,
  onDoubleTap,
  isEnabled = true,
  targetRef,
}: UseTouchGesturesOptions) {
  const initialTouchesRef = useRef<TouchPoint[]>([]);
  const initialDistanceRef = useRef<number>(0);
  const lastTapTimeRef = useRef<number>(0);
  const lastTouchEndRef = useRef<number>(0);

  useEffect(() => {
    if (!isEnabled) return;

    const target = targetRef?.current || document;

    const getDistance = (touch1: Touch, touch2: Touch): number => {
      const dx = touch1.clientX - touch2.clientX;
      const dy = touch1.clientY - touch2.clientY;
      return Math.sqrt(dx * dx + dy * dy);
    };

    const getCenter = (touches: TouchPoint[]): { x: number; y: number } => {
      if (touches.length === 0) return { x: 0, y: 0 };
      const sum = touches.reduce((acc, touch) => ({ x: acc.x + touch.x, y: acc.y + touch.y }), { x: 0, y: 0 });
      return { x: sum.x / touches.length, y: sum.y / touches.length };
    };

    const handleTouchStart = (e: Event) => {
      const touchEvent = e as TouchEvent;
      if (touchEvent.touches.length === 2 && onPinch) {
        // Pinch-to-zoom start
        const touch1 = touchEvent.touches[0];
        const touch2 = touchEvent.touches[1];

        initialTouchesRef.current = [
          { x: touch1.clientX, y: touch1.clientY, identifier: touch1.identifier },
          { x: touch2.clientX, y: touch2.clientY, identifier: touch2.identifier },
        ];
        initialDistanceRef.current = getDistance(touch1, touch2);
      } else if (touchEvent.touches.length === 1) {
        // Potential tap or pan start
        const touch = touchEvent.touches[0];
        initialTouchesRef.current = [
          { x: touch.clientX, y: touch.clientY, identifier: touch.identifier },
        ];
      }
    };

    const handleTouchMove = (e: Event) => {
      const touchEvent = e as TouchEvent;
      if (touchEvent.touches.length === 2 && onPinch) {
        // Pinch-to-zoom
        const touch1 = touchEvent.touches[0];
        const touch2 = touchEvent.touches[1];
        const currentDistance = getDistance(touch1, touch2);

        if (initialDistanceRef.current > 0) {
          const scale = currentDistance / initialDistanceRef.current;
          const center = getCenter([
            { x: touch1.clientX, y: touch1.clientY, identifier: touch1.identifier },
            { x: touch2.clientX, y: touch2.clientY, identifier: touch2.identifier },
          ]);

          onPinch(scale, center.x, center.y);
        }
      } else if (touchEvent.touches.length === 1 && onPan && initialTouchesRef.current.length === 1) {
        // Pan
        const touch = touchEvent.touches[0];
        const initialTouch = initialTouchesRef.current[0];
        const deltaX = touch.clientX - initialTouch.x;
        const deltaY = touch.clientY - initialTouch.y;

        onPan(deltaX, deltaY);

        // Update initial touch for continuous panning
        initialTouchesRef.current = [
          { x: touch.clientX, y: touch.clientY, identifier: touch.identifier },
        ];
      }
    };

    const handleTouchEnd = (e: Event) => {
      const touchEvent = e as TouchEvent;
      const now = Date.now();

      if (touchEvent.changedTouches.length === 1 && onTap) {
        // Check for tap or double tap
        const timeSinceLastTap = now - lastTapTimeRef.current;
        const touch = touchEvent.changedTouches[0];

        if (timeSinceLastTap < 300 && timeSinceLastTap > 0) {
          // Double tap
          if (onDoubleTap) {
            onDoubleTap(touch.clientX, touch.clientY);
          }
        } else if (now - lastTouchEndRef.current < 300) {
          // Single tap
          onTap(touch.clientX, touch.clientY);
        }

        lastTapTimeRef.current = now;
      }

      lastTouchEndRef.current = now;

      // Reset pinch state
      if (touchEvent.touches.length < 2) {
        initialDistanceRef.current = 0;
        initialTouchesRef.current = [];
      }
    };

    target.addEventListener('touchstart', handleTouchStart, { passive: true });
    target.addEventListener('touchmove', handleTouchMove, { passive: true });
    target.addEventListener('touchend', handleTouchEnd, { passive: true });
    target.addEventListener('touchcancel', handleTouchEnd, { passive: true });

    return () => {
      target.removeEventListener('touchstart', handleTouchStart);
      target.removeEventListener('touchmove', handleTouchMove);
      target.removeEventListener('touchend', handleTouchEnd);
      target.removeEventListener('touchcancel', handleTouchEnd);
    };
  }, [isEnabled, onPinch, onPan, onTap, onDoubleTap, targetRef]);
}

// Специализированный хук для ReactFlow zoom/pan
export interface UseReactFlowTouchGesturesOptions {
  fitView?: () => void;
  setViewport?: (x: number, y: number, zoom: number) => void;
  getViewport?: () => { x: number; y: number; zoom: number };
  isEnabled?: boolean;
}

export function useReactFlowTouchGestures({
  fitView,
  setViewport,
  getViewport,
  isEnabled = true,
}: UseReactFlowTouchGesturesOptions) {
  useTouchGestures({
    isEnabled,
    onPinch: (scale) => {
      if (!getViewport || !setViewport) return;

      const current = getViewport();
      const newZoom = Math.min(Math.max(current.zoom * scale, 0.1), 4);

      setViewport(current.x, current.y, newZoom);
    },
    onPan: (deltaX, deltaY) => {
      if (!getViewport || !setViewport) return;

      const current = getViewport();
      const newX = current.x - deltaX / current.zoom;
      const newY = current.y - deltaY / current.zoom;

      setViewport(newX, newY, current.zoom);
    },
    onDoubleTap: () => {
      if (fitView) {
        fitView();
      }
    },
  });
}
