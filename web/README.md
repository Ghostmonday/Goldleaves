# Goldleaves Web UI

A modern React application featuring hero animations and smooth route transitions using Framer Motion.

## Features

### 🎬 Route Transitions
- Smooth page transitions with scale and opacity animations
- Customizable transition timing and easing
- Non-blocking animations using AnimatePresence

### 🦸 Hero Animations
- Shared element transitions between routes
- Layout animations for seamless morphing
- Support for text, images, and custom elements

### 🏗 Architecture
- React 18 with TypeScript
- Vite for fast development and building
- React Router for routing
- Framer Motion for animations

## Getting Started

```bash
# Install dependencies
npm install

# Start development server
npm run dev

# Build for production
npm run build

# Preview production build
npm run preview
```

## Components

### RouteTransition
Wrapper component that provides smooth animations between route changes.

```tsx
import { RouteTransition } from './components/RouteTransition'

<RouteTransition>
  <YourPageComponent />
</RouteTransition>
```

### Hero Elements
Components for creating shared element transitions between routes.

```tsx
import { HeroElement, HeroText, HeroImage } from './components/HeroAnimations'

// Shared element that animates between routes
<HeroElement id="unique-id">
  <div>Content that transitions</div>
</HeroElement>

// Text with layout animations
<HeroText id="title" as="h1">
  Page Title
</HeroText>

// Image with transitions
<HeroImage id="hero-image" src="/image.jpg" alt="Hero" />
```

## Animation Types

1. **Route Transitions**: Page-level animations when navigating between routes
2. **Hero Animations**: Element-level animations using shared layout IDs
3. **Entrance Animations**: Staggered animations for page content
4. **Hover Effects**: Interactive animations on user interaction

## Configuration

The route transition behavior can be customized in `RouteTransition.tsx`:

```tsx
const routeVariants = {
  initial: { opacity: 0, scale: 0.95, y: 20 },
  in: { opacity: 1, scale: 1, y: 0 },
  out: { opacity: 0, scale: 1.05, y: -20 },
}

const routeTransition = {
  type: 'tween',
  ease: 'anticipate',
  duration: 0.4,
}
```

## Best Practices

1. **Use consistent layoutId values** for hero elements that should transition between routes
2. **Keep animations performant** by animating transform and opacity properties
3. **Provide fallbacks** for reduced motion preferences
4. **Test on different devices** to ensure smooth performance

## Integration with Backend

The application is configured to proxy API requests to the FastAPI backend:

```typescript
// vite.config.ts
proxy: {
  '/api': {
    target: 'http://localhost:8000',
    changeOrigin: true,
    secure: false,
  },
}
```

## Browser Support

- Modern browsers with ES2020 support
- CSS transforms and animations
- Framer Motion compatibility

## Performance Considerations

- Animations use GPU acceleration when possible
- Components are optimized for re-renders
- Bundle size is optimized with tree shaking
- Images and assets are lazy-loaded where appropriate
