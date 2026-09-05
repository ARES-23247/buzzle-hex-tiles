// BUZZLE 217-Cell Board Definition (Radius 8)
export const BUZZLE_RADIUS = 8;
export const BUZZLE_CELL_COUNT = 217;

export const TRIPLE_WORD_KEYS = new Set<string>(["-8,0", "0,-8", "-8,8", "8,-8", "0,8", "8,0"]);
export const TRIPLE_LETTER_KEYS = new Set<string>(["-4,-4", "-8,4", "4,-8", "-4,8", "8,-4", "4,4"]);
export const DOUBLE_WORD_KEYS = new Set<string>(["-6,-1", "-1,-6", "-7,1", "1,-7", "-7,6", "6,-7", "-6,7", "7,-6", "-1,7", "7,-1", "1,6", "6,1"]);
export const KEY_WILD_KEYS = new Set<string>(["-2,-2", "-4,2", "2,-4", "-2,4", "4,-2", "2,2"]);
export const DOUBLE_LETTER_KEYS = new Set<string>(["-4,-2", "-2,-4", "-6,2", "-4,0", "0,-4", "2,-6", "-6,4", "-1,-1", "4,-6", "-2,1", "1,-2", "-4,4", "4,-4", "-1,2", "2,-1", "-4,6", "1,1", "6,-4", "-2,6", "0,4", "4,0", "6,-2", "2,4", "4,2"]);
