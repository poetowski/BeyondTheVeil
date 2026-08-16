import { ConsumableIcon } from "./ConsumableIcon";
import { ItemIcon } from "./ItemIcon";
import { RuneIcon } from "./RuneIcon";

interface RecipeOutputIconProps {
  outputType: "consumable" | "rune" | "item";
  slug: string;
  name: string;
}

export function RecipeOutputIcon({ outputType, slug, name }: RecipeOutputIconProps) {
  if (outputType === "item") return <ItemIcon slug={slug} name={name} />;
  if (outputType === "rune") return <RuneIcon slug={slug} name={name} />;
  return <ConsumableIcon slug={slug} name={name} />;
}
