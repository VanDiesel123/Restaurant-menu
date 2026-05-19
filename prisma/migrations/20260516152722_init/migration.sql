-- CreateEnum
CREATE TYPE "OrderType" AS ENUM ('IN_RESTAURANT', 'TAKEAWAY');

-- CreateTable
CREATE TABLE "Ingredient" (
    "Ingredient_id" SERIAL NOT NULL,
    "Ing_name" TEXT NOT NULL,

    CONSTRAINT "Ingredient_pkey" PRIMARY KEY ("Ingredient_id")
);

-- CreateTable
CREATE TABLE "Dish" (
    "Dish_id" SERIAL NOT NULL,
    "Dish_name" TEXT NOT NULL,
    "Price" DOUBLE PRECISION NOT NULL,

    CONSTRAINT "Dish_pkey" PRIMARY KEY ("Dish_id")
);

-- CreateTable
CREATE TABLE "Order" (
    "Order_id" SERIAL NOT NULL,
    "Table_name" INTEGER,
    "Order_type" "OrderType" NOT NULL,
    "Total_price" DOUBLE PRECISION NOT NULL,
    "Create_time" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT "Order_pkey" PRIMARY KEY ("Order_id")
);

-- CreateTable
CREATE TABLE "DishIngredient" (
    "DishId" INTEGER NOT NULL,
    "IngredientId" INTEGER NOT NULL,

    CONSTRAINT "DishIngredient_pkey" PRIMARY KEY ("DishId","IngredientId")
);

-- CreateTable
CREATE TABLE "OrderItem" (
    "OrderItem_id" SERIAL NOT NULL,
    "OrderId" INTEGER NOT NULL,
    "DishId" INTEGER NOT NULL,
    "Quantity" INTEGER NOT NULL,

    CONSTRAINT "OrderItem_pkey" PRIMARY KEY ("OrderItem_id")
);

-- CreateIndex
CREATE UNIQUE INDEX "Ingredient_Ing_name_key" ON "Ingredient"("Ing_name");

-- CreateIndex
CREATE UNIQUE INDEX "Dish_Dish_name_key" ON "Dish"("Dish_name");

-- AddForeignKey
ALTER TABLE "DishIngredient" ADD CONSTRAINT "DishIngredient_DishId_fkey" FOREIGN KEY ("DishId") REFERENCES "Dish"("Dish_id") ON DELETE RESTRICT ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "DishIngredient" ADD CONSTRAINT "DishIngredient_IngredientId_fkey" FOREIGN KEY ("IngredientId") REFERENCES "Ingredient"("Ingredient_id") ON DELETE RESTRICT ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "OrderItem" ADD CONSTRAINT "OrderItem_OrderId_fkey" FOREIGN KEY ("OrderId") REFERENCES "Order"("Order_id") ON DELETE RESTRICT ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "OrderItem" ADD CONSTRAINT "OrderItem_DishId_fkey" FOREIGN KEY ("DishId") REFERENCES "Dish"("Dish_id") ON DELETE RESTRICT ON UPDATE CASCADE;
