-- AlterTable
ALTER TABLE "Dish" ADD COLUMN     "Cooking_time" INTEGER NOT NULL DEFAULT 25;

-- CreateTable
CREATE TABLE "RecipeItem" (
    "id" SERIAL NOT NULL,
    "dish_name" TEXT NOT NULL,
    "ing_name" TEXT NOT NULL,
    "meta_data" TEXT NOT NULL,

    CONSTRAINT "RecipeItem_pkey" PRIMARY KEY ("id")
);
