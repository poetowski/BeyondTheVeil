import { useState } from "react";

interface RuneIconProps {
  slug: string;
  name: string;
}

export function RuneIcon({ slug, name }: RuneIconProps) {
  const [missing, setMissing] = useState(false);
  if (missing) {
    return <div className="item-icon item-icon--missing" aria-hidden="true" />;
  }
  return (
    <img
      className="item-icon"
      src={`/runes/${slug}.svg`}
      alt={name}
      onError={() => setMissing(true)}
    />
  );
}
