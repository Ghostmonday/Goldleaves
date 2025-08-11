export interface NavigationRoute {
  label: string;
  href: string;
  icon?: string;
}

export const navigationRoutes: NavigationRoute[] = [
  {
    label: 'Dashboard',
    href: '/',
  },
  {
    label: 'Usage',
    href: '/usage',
  },
  {
    label: 'Documents',
    href: '/documents',
  },
  {
    label: 'Settings',
    href: '/settings',
  },
];