"use client";

import { memo } from 'react';

import type { Reading } from '@/lib/types';
import { MeterCard } from './MeterCard';

interface MeterListItemProps {
    reading: Reading;
    onClick?: () => void;
    onEdit?: (reading: Reading) => void;
    onMeta?: (reading: Reading) => void;
    onDelete?: (meter_id: string) => void;
}

// List view = the same ISA-101 meter card condensed into a row (data-view="list").
export const MeterListItem = memo((props: MeterListItemProps) => <MeterCard compact {...props} />);

MeterListItem.displayName = 'MeterListItem';
