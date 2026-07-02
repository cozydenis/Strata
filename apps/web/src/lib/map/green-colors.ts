/**
 * Green-space polygon layer palette.
 *
 * Sourced from Strata's functional palette (see globals.css):
 *   fill    -> sage (--strata-sage, #8FA071) at low opacity — ambient context
 *   outline -> a slightly darker sage for a subtle 1px edge
 */

/** Muted sage fill — matches --strata-sage in globals.css. */
export const GREEN_FILL_COLOR = '#8FA071';

/** Low fill opacity so polygons read as ambient context, not a choropleth. */
export const GREEN_FILL_OPACITY = 0.35;

/** Slightly darker sage for the polygon outline. */
export const GREEN_OUTLINE_COLOR = '#75855B';

/** Hairline outline width in px. */
export const GREEN_OUTLINE_WIDTH = 1;
