declare module "@/components/ui/tooltip" {
  export interface TooltipProps {
    content: React.ReactNode;
    children: React.ReactNode;
    className?: string;
  }
  export const Tooltip: React.FC<TooltipProps>;
}

declare module "@/components/ui/switch" {
  import * as React from "react";
  export interface SwitchProps extends React.ComponentPropsWithoutRef<"button"> {
    checked?: boolean;
    onCheckedChange?: (checked: boolean) => void;
  }
  export const Switch: React.ForwardRefExoticComponent<SwitchProps>;
}

declare module "@/components/ui/label" {
  import * as React from "react";
  export interface LabelProps extends React.ComponentPropsWithoutRef<"label"> {}
  export const Label: React.ForwardRefExoticComponent<LabelProps>;
}

declare module "@/components/ui/select" {
  import * as React from "react";
  
  export interface SelectProps {
    value?: string;
    onValueChange?: (value: string) => void;
    children: React.ReactNode;
  }

  export const Select: React.FC<SelectProps>;
  export const SelectContent: React.FC<{ children: React.ReactNode }>;
  export const SelectItem: React.FC<{ value: string; children: React.ReactNode }>;
  export const SelectTrigger: React.FC<{ id?: string; className?: string; children: React.ReactNode }>;
  export const SelectValue: React.FC<{ placeholder?: string }>;
}