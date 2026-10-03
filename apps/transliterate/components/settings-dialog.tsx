"use client";

import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  isReadingStyle,
  READING_STYLE_LABELS,
  READING_STYLES,
  type ReadingStyle,
} from "@/lib/preferences";

interface SettingsDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  style: ReadingStyle;
  onStyleChange: (style: ReadingStyle) => void;
}

export function SettingsDialog({
  open,
  onOpenChange,
  style,
  onStyleChange,
}: SettingsDialogProps) {
  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Settings</DialogTitle>
          <DialogDescription>
            Choose how transliterated text is shown: romaji, furigana, or both.
          </DialogDescription>
        </DialogHeader>
        <div>
          <p className="mb-2 text-sm font-medium">
            <label htmlFor="reading-style">Reading aid</label>
          </p>
          <Select
            value={style}
            items={Object.fromEntries(
              READING_STYLES.map((entry) => [
                entry,
                READING_STYLE_LABELS[entry],
              ]),
            )}
            onValueChange={(value) => {
              if (isReadingStyle(value)) onStyleChange(value);
            }}
          >
            <SelectTrigger id="reading-style" className="w-full">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              {READING_STYLES.map((entry) => (
                <SelectItem key={entry} value={entry}>
                  {READING_STYLE_LABELS[entry]}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>
      </DialogContent>
    </Dialog>
  );
}
