/**
 * Bot Constructor Theme Design System
 * Unified color palette for Bot Constructor Admin Panel
 */

export const theme = {
  colors: {
    // Primary - Blue
    brand: {
      50: '#eff6ff',
      100: '#dbeafe',
      200: '#bfdbfe',
      300: '#93c5fd',
      400: '#60a5fa',
      500: '#3b82f6', // Main blue
      600: '#2563eb',
      700: '#1d4ed8',
      800: '#1e40af',
      900: '#1e3a8a',
    },

    // Secondary - Emerald
    accent: {
      50: '#ecfdf5',
      100: '#d1fae5',
      200: '#a7f3d0',
      300: '#6ee7b7',
      400: '#34d399',
      500: '#10b981', // Main emerald
      600: '#059669',
      700: '#047857',
      800: '#065f46',
      900: '#064e3b',
    },

    // Highlight - Amber
    highlight: {
      50: '#fffbeb',
      100: '#fef3c7',
      200: '#fde68a',
      300: '#fcd34d',
      400: '#fbbf24',
      500: '#f59e0b', // Main amber
      600: '#d97706',
      700: '#b45309',
      800: '#92400e',
      900: '#78350f',
    },

    // Node-specific colors (derived from brand palette with different hues)
    nodes: {
      text: {
        border: '#3b82f6',     // Brand
        bg: '#eff6ff',         // Brand 50
        bgDark: 'rgba(59, 130, 246, 0.1)',
        icon: '#3b82f6',
        text: '#1d4ed8',       // Brand 700
        textDark: '#93c5fd',   // Brand 300
      },
      video: {
        border: '#2563eb',     // Brand 600
        bg: '#dbeafe',         // Brand 100
        bgDark: 'rgba(37, 99, 235, 0.1)',
        icon: '#2563eb',
        text: '#1d4ed8',
        textDark: '#bfdbfe',   // Brand 200
      },
      quiz: {
        border: '#f59e0b',     // Highlight
        bg: '#fffbeb',         // Highlight 50
        bgDark: 'rgba(245, 158, 11, 0.1)',
        icon: '#f59e0b',
        text: '#b45309',       // Highlight 700
        textDark: '#fbbf24',   // Highlight 400
      },
      decision: {
        border: '#d97706',     // Highlight 600
        bg: '#fef3c7',         // Highlight 100
        bgDark: 'rgba(217, 119, 6, 0.1)',
        icon: '#d97706',
        text: '#b45309',
        textDark: '#fcd34d',   // Highlight 300
      },
      menu: {
        border: '#10b981',     // Accent
        bg: '#ecfdf5',         // Accent 50
        bgDark: 'rgba(16, 185, 129, 0.1)',
        icon: '#10b981',
        text: '#047857',       // Accent 700
        textDark: '#6ee7b7',   // Accent 300
      },
      start: {
        border: '#10b981',     // Accent
        bg: '#ecfdf5',         // Accent 50
        bgDark: 'rgba(16, 185, 129, 0.1)',
        icon: '#10b981',
        text: '#047857',
        textDark: '#6ee7b7',
      },
      end: {
        border: '#3b82f6',     // Brand
        bg: '#eff6ff',         // Brand 50
        bgDark: 'rgba(59, 130, 246, 0.1)',
        icon: '#3b82f6',
        text: '#1d4ed8',
        textDark: '#93c5fd',
      },
      payment: {
        border: '#f59e0b',     // Highlight
        bg: '#fffbeb',         // Highlight 50
        bgDark: 'rgba(245, 158, 11, 0.1)',
        icon: '#f59e0b',
        text: '#b45309',
        textDark: '#fbbf24',
      },
    },

    // Buttons
    buttons: {
      primary: '#3b82f6',      // Brand
      primaryHover: '#2563eb',
      secondary: '#10b981',    // Accent
      secondaryHover: '#059669',
      accent: '#f59e0b',       // Highlight
      accentHover: '#d97706',
      danger: '#dc2626',
      dangerHover: '#b91c1c',
    },
  },

  // Common styles for consistency
  styles: {
    node: {
      width: 'w-48',
      borderRadius: 'rounded-lg',
      border: 'border-2',
      padding: 'px-4 py-3',
      shadow: 'shadow-md',
      header: {
        marginBottom: 'mb-2',
        display: 'flex',
        alignItems: 'items-center',
        gap: 'gap-2',
      },
      icon: {
        rounded: 'rounded',
        padding: 'p-1',
      },
      label: {
        fontSize: 'text-sm',
        fontWeight: 'font-semibold',
      },
      description: {
        fontSize: 'text-xs',
        textColor: 'text-gray-600',
        textColorDark: 'dark:text-gray-400',
        truncate: 'truncate',
      },
    },
  },
};

// Export individual color maps for convenience
export const nodeColors = theme.colors.nodes;
export const buttonColors = theme.colors.buttons;
export const brandColors = theme.colors.brand;
export const accentColors = theme.colors.accent;
export const highlightColors = theme.colors.highlight;
