"use client";

import { useState } from "react";
import { Calendar as CalendarIcon } from "lucide-react";
import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/button";
import { Calendar } from "@/components/ui/calendar";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
    Popover,
    PopoverContent,
    PopoverTrigger,
} from "@/components/ui/popover";

/**
 * UTC wall-clock date+time picker.
 *
 * `value` / `onChange` use a tz-naive `YYYY-MM-DDTHH:mm:ss` string treated as
 * UTC by the caller — keeping the deterministic run stable across browser
 * locales. The Calendar only contributes Y/M/D (read via local Date getters,
 * which match the day the user clicked); the time Input supplies HH:mm:ss.
 */
interface DateTimePickerProps {
    value: string;
    onChange: (value: string) => void;
    className?: string;
    "aria-label"?: string;
}

const pad = (n: number) => String(n).padStart(2, "0");

// Stable fallback date for the (unreachable in practice) case where the time
// input changes before any day is selected — avoids a non-deterministic
// `new Date()` in the render path. Fixed args => evaluated once, deterministic.
const FALLBACK_DATE = new Date(2026, 0, 1);

function parseValue(value: string): { date?: Date; time: string } {
    const [datePart, timePart] = value.split("T");
    const time = (timePart ?? "00:00:00").slice(0, 8).padEnd(8, "0").slice(0, 8);
    if (datePart) {
        const [y, m, d] = datePart.split("-").map(Number);
        if (y && m && d) return { date: new Date(y, m - 1, d), time };
    }
    return { time };
}

function compose(date: Date, time: string): string {
    return `${date.getFullYear()}-${pad(date.getMonth() + 1)}-${pad(date.getDate())}T${time}`;
}

export function DateTimePicker({ value, onChange, className, ...rest }: DateTimePickerProps) {
    const [open, setOpen] = useState(false);
    const { date, time } = parseValue(value);

    return (
        <Popover open={open} onOpenChange={setOpen}>
            <PopoverTrigger
                render={
                    <Button
                        type="button"
                        variant="outline"
                        size="sm"
                        aria-label={rest["aria-label"]}
                        className={cn("justify-start gap-1 font-mono text-xs", className)}
                    >
                        <CalendarIcon className="h-3 w-3" />
                        {value ? value.replace("T", " ") : "Pick date"}
                        <span className="ml-1 text-[9px] font-bold text-muted-foreground">UTC</span>
                    </Button>
                }
            />
            <PopoverContent className="w-auto p-0" align="start">
                <Calendar
                    mode="single"
                    selected={date}
                    onSelect={(d) => {
                        if (d) onChange(compose(d, time));
                    }}
                    autoFocus
                />
                <div className="flex items-center gap-2 border-t p-3">
                    <Label htmlFor="dtp-time" className="text-xs whitespace-nowrap">
                        Time (UTC)
                    </Label>
                    <Input
                        id="dtp-time"
                        type="time"
                        step="1"
                        value={time}
                        onChange={(e) =>
                            onChange(compose(date ?? FALLBACK_DATE, e.target.value || "00:00:00"))
                        }
                        className="w-32"
                    />
                </div>
            </PopoverContent>
        </Popover>
    );
}
