'use client';

import * as React from 'react';
import './popover.css';
import {
  useFloating,
  flip,
  shift,
  useClick,
  useRole,
  useInteractions,
  FloatingPortal,
  FloatingOverlay,
  FloatingFocusManager,
  useDismiss,
  Placement,
  Middleware,
} from '@floating-ui/react';

import { cn } from '@/lib/utils';

interface PopoverProps extends React.HTMLAttributes<HTMLDivElement> {
  open?: boolean;
  onOpenChange?: (open: boolean) => void;
}

const Popover = React.forwardRef<HTMLDivElement, PopoverProps>(
  ({ className, children, ...props }, ref) => (
    <div className={cn('relative', className)} ref={ref} {...props}>
      {children}
    </div>
  )
);
Popover.displayName = 'Popover';

interface PopoverTriggerProps
  extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  asChild?: boolean;
}

const PopoverTrigger = React.forwardRef<
  HTMLButtonElement,
  PopoverTriggerProps
>(({ className, children, asChild = false, ...props }, ref) => {
  const Component = asChild ? React.Fragment : 'button';
  return (
    <Component
      ref={ref}
      className={cn('text-sm', className)}
      {...props}
    >
      {children}
    </Component>
  );
});
PopoverTrigger.displayName = 'PopoverTrigger';

interface PopoverContentProps
  extends React.HTMLAttributes<HTMLDivElement> {
  sideOffset?: number;
  align?: 'start' | 'center' | 'end';
  placement?: Placement;
  middleware?: Middleware[];
}

const PopoverContent = React.forwardRef<
  HTMLDivElement,
  PopoverContentProps
>(
  (
    {
      className,
      children,
      sideOffset = 4,
      align = 'center',
      placement = 'bottom',
      middleware = [],
      ...props
    },
    ref
  ) => {
    const { context } = useFloating({
      placement,
      middleware: [
        flip(),
        shift({ padding: 8 }),
        ...middleware
      ],
    });

    const click = useClick(context);
    const role = useRole(context, { role: 'dialog' });
    const dismiss = useDismiss(context);

    const { getFloatingProps } = useInteractions([
      click,
      role,
      dismiss,
    ]);

    return (
      <FloatingPortal>
        <FloatingOverlay
          className="fixed inset-0 z-50 bg-black/50"
          style={{ display: context.open ? 'block' : 'none' }}
        />
        <FloatingFocusManager context={context} modal={true}>
          <div
            ref={ref}
            className={cn(
                'popover-content',
                className 
            )}
            {...props}
            {...getFloatingProps()}
          >
            {children}
          </div>
        </FloatingFocusManager>
      </FloatingPortal>
    );
  }
);
PopoverContent.displayName = 'PopoverContent';

export { Popover, PopoverTrigger, PopoverContent };