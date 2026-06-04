"use client";

import React, { useEffect, useState } from 'react';

/**
 * Ensures that the wrapped children are only rendered on the client.
 * This is crucial for components that use client-side hooks like useState,
 * especially when they are part of a shared layout that might be 
 * rendered during build-time (prerendering) or on the server (SSR).
 */
export function ClientOnly({ children }: { children: React.ReactNode }) {
    const [hasMounted, setHasMounted] = useState(false);

    useEffect(() => {
        setHasMounted(true);
    }, []);

    if (!hasMounted) {
        return null;
    }

    return <>{children}</>;
}
