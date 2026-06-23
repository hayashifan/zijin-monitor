import { useRef, useEffect, useState } from 'react';

/**
 * 值变化闪烁 hook — 当值改变时返回 true，动画结束后恢复 false
 * 用于数字变动时的轻动效
 */
export function useValueFlash(value: number | string, delay = 600): boolean {
  const [flash, setFlash] = useState(false);
  const prevRef = useRef(value);
  const timerRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  useEffect(() => {
    if (prevRef.current !== value) {
      prevRef.current = value;
      setFlash(true);
      if (timerRef.current) clearTimeout(timerRef.current);
      timerRef.current = setTimeout(() => setFlash(false), delay);
    }
    return () => { if (timerRef.current) clearTimeout(timerRef.current); };
  }, [value, delay]);

  return flash;
}

/**
 * 批量值变化检测 — 传入一组值，返回哪些发生了变化
 */
export function useMultiFlash<T extends Record<string, number | string>>(
  values: T,
  delay = 600
): Record<keyof T, boolean> {
  const [flashes, setFlashes] = useState<Record<string, boolean>>({});
  const prevRef = useRef(values);
  const timerRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  useEffect(() => {
    const changed: Record<string, boolean> = {};
    let hasChange = false;
    for (const key of Object.keys(values)) {
      if (prevRef.current[key] !== values[key]) {
        changed[key] = true;
        hasChange = true;
      }
    }
    prevRef.current = values;

    if (hasChange) {
      setFlashes(changed);
      if (timerRef.current) clearTimeout(timerRef.current);
      timerRef.current = setTimeout(() => setFlashes({}), delay);
    }
    return () => { if (timerRef.current) clearTimeout(timerRef.current); };
  }, [values, delay]);

  return flashes as Record<keyof T, boolean>;
}
