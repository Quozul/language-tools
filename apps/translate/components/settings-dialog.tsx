"use client";

import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "@qzl/ui/components/dialog";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@qzl/ui/components/select";
import { Toggle } from "@qzl/ui/components/toggle";
import {
  familyById,
  isModelPreset,
  MODEL_FAMILIES,
  MODEL_PRESET_LABELS,
  MODEL_PRESETS,
  type ModelFamilyId,
  type ModelPreset,
} from "@/lib/models";

interface SettingsDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  family: ModelFamilyId;
  preset: ModelPreset;
  debugInfo: boolean;
  onFamilyChange: (family: ModelFamilyId) => void;
  onPresetChange: (preset: ModelPreset) => void;
  onDebugInfoChange: (debugInfo: boolean) => void;
}

export function SettingsDialog({
  open,
  onOpenChange,
  family,
  preset,
  debugInfo,
  onFamilyChange,
  onPresetChange,
  onDebugInfoChange,
}: SettingsDialogProps) {
  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Settings</DialogTitle>
          <DialogDescription>
            Configure the settings for the app.
          </DialogDescription>
        </DialogHeader>
        <div className="flex flex-col gap-4">
          <div>
            <p className="mb-2 text-sm font-medium">
              <label htmlFor="model-family">Model family</label>
            </p>
            <Select
              value={family}
              items={Object.fromEntries(
                MODEL_FAMILIES.map((entry) => [entry.id, entry.name]),
              )}
              onValueChange={(value) => {
                if (value === null) return;
                const matched = familyById(value);
                if (matched) onFamilyChange(matched.id);
              }}
            >
              <SelectTrigger id="model-family" className="w-full">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                {MODEL_FAMILIES.map((entry) => (
                  <SelectItem key={entry.id} value={entry.id}>
                    {entry.name}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
          <div>
            <p className="mb-2 text-sm font-medium">
              <label htmlFor="model-preset">Model</label>
            </p>
            <Select
              value={preset}
              items={Object.fromEntries(
                MODEL_PRESETS.map((entry) => [
                  entry,
                  MODEL_PRESET_LABELS[entry],
                ]),
              )}
              onValueChange={(value) => {
                if (value !== null && isModelPreset(value))
                  onPresetChange(value);
              }}
            >
              <SelectTrigger
                id="model-preset"
                className="w-full"
                aria-describedby="model-preset-detail"
              >
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                {MODEL_PRESETS.map((entry) => (
                  <SelectItem key={entry} value={entry}>
                    {MODEL_PRESET_LABELS[entry]}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
          <div className="flex items-center justify-between gap-4">
            <div>
              <p className="text-sm font-medium">
                <label htmlFor="debug-info">Debug info</label>
              </p>
              <p
                id="debug-info-detail"
                className="text-sm text-muted-foreground"
              >
                Show model, duration, and cache state after each translation.
              </p>
            </div>
            <Toggle
              id="debug-info"
              pressed={debugInfo}
              onPressedChange={(pressed) => onDebugInfoChange(pressed)}
              aria-describedby="debug-info-detail"
            >
              {debugInfo ? "On" : "Off"}
            </Toggle>
          </div>
        </div>
      </DialogContent>
    </Dialog>
  );
}
