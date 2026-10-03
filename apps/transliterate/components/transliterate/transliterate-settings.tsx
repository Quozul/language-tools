"use client";

import { EllipsisVerticalIcon } from "lucide-react";
import { useEffect, useState } from "react";
import { SettingsDialog } from "@/components/settings-dialog";
import { Button } from "@/components/ui/button";
import { Kbd, KbdGroup } from "@/components/ui/kbd";
import {
  Tooltip,
  TooltipContent,
  TooltipTrigger,
} from "@/components/ui/tooltip";
import {
  useTransliterateActions,
  useTransliterateSettings,
} from "./transliterate-context";

export function TransliterateSettings() {
  const { style } = useTransliterateSettings();
  const { changeStyle } = useTransliterateActions();
  const [open, setOpen] = useState(false);

  useEffect(() => {
    const onKeyDown = (event: KeyboardEvent) => {
      if ((event.ctrlKey || event.metaKey) && event.key === ",") {
        event.preventDefault();
        setOpen(true);
      }
    };
    window.addEventListener("keydown", onKeyDown);
    return () => window.removeEventListener("keydown", onKeyDown);
  }, []);

  return (
    <>
      <Tooltip>
        <TooltipTrigger
          render={
            <Button
              type="button"
              variant="ghost"
              size="icon"
              aria-label="Settings"
              onClick={() => setOpen(true)}
            />
          }
        >
          <EllipsisVerticalIcon />
        </TooltipTrigger>
        <TooltipContent side="bottom">
          Settings
          <KbdGroup>
            <Kbd>Ctrl</Kbd>
            <Kbd>,</Kbd>
          </KbdGroup>
        </TooltipContent>
      </Tooltip>
      <SettingsDialog
        open={open}
        onOpenChange={setOpen}
        style={style}
        onStyleChange={changeStyle}
      />
    </>
  );
}
