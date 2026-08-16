import { useState } from "react";

interface ConsumableIconProps {
  slug: string;
  name: string;
}

export function ConsumableIcon({ slug, name }: ConsumableIconProps) {
  const [missing, setMissing] = useState(false);
  if (missing) {
    return <div className="item-icon item-icon--missing" aria-hidden="true" />;
  }
  return (
    <img
      className="item-icon"
      src={`/consumables/${slug}.svg`}
      alt={name}
      onError={() => setMissing(true)}
    />
  );
}
