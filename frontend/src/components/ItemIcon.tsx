import { useState } from "react";

interface ItemIconProps {
  slug: string;
  name: string;
}

export function ItemIcon({ slug, name }: ItemIconProps) {
  const [missing, setMissing] = useState(false);
  if (missing) {
    return <div className="item-icon item-icon--missing" aria-hidden="true" />;
  }
  return (
    <img
      className="item-icon"
      src={`/items/${slug}.svg`}
      alt={name}
      onError={() => setMissing(true)}
    />
  );
}
