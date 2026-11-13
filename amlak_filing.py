#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
نرم‌افزار فایلینگ املاک
Real Estate Property Filing Software
"""

import customtkinter as ctk
from tkinter import ttk, messagebox, filedialog
import sqlite3
import os
from datetime import datetime
import csv

# تنظیمات ظاهری
ctk.set_appearance_mode("light")
ctk.set_default_color_theme("blue")

DB_NAME = "amlak_data.db"


class Database:
    def __init__(self):
        self.conn = sqlite3.connect(DB_NAME)
        self.create_table()

    def create_table(self):
        cursor = self.conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS properties (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                property_type TEXT,
                deal_type TEXT,
                price REAL,
                area REAL,
                rooms INTEGER,
                floor TEXT,
                year_built INTEGER,
                address TEXT,
                city TEXT,
                neighborhood TEXT,
                status TEXT,
                owner_name TEXT,
                owner_phone TEXT,
                description TEXT,
                created_at TEXT,
                updated_at TEXT
            )
        """)
        self.conn.commit()

    def add_property(self, data):
        cursor = self.conn.cursor()
        now = datetime.now().strftime("%Y-%m-%d %H:%M")
        cursor.execute("""
            INSERT INTO properties (
                title, property_type, deal_type, price, area, rooms, floor,
                year_built, address, city, neighborhood, status,
                owner_name, owner_phone, description, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            data["title"], data["property_type"], data["deal_type"],
            data["price"], data["area"], data["rooms"], data["floor"],
            data["year_built"], data["address"], data["city"],
            data["neighborhood"], data["status"], data["owner_name"],
            data["owner_phone"], data["description"], now, now
        ))
        self.conn.commit()
        return cursor.lastrowid

    def update_property(self, prop_id, data):
        cursor = self.conn.cursor()
        now = datetime.now().strftime("%Y-%m-%d %H:%M")
        cursor.execute("""
            UPDATE properties SET
                title=?, property_type=?, deal_type=?, price=?, area=?, rooms=?,
                floor=?, year_built=?, address=?, city=?, neighborhood=?,
                status=?, owner_name=?, owner_phone=?, description=?, updated_at=?
            WHERE id=?
        """, (
            data["title"], data["property_type"], data["deal_type"],
            data["price"], data["area"], data["rooms"], data["floor"],
            data["year_built"], data["address"], data["city"],
            data["neighborhood"], data["status"], data["owner_name"],
            data["owner_phone"], data["description"], now, prop_id
        ))
        self.conn.commit()

    def delete_property(self, prop_id):
        cursor = self.conn.cursor()
        cursor.execute("DELETE FROM properties WHERE id=?", (prop_id,))
        self.conn.commit()

    def get_all(self, search="", filters=None):
        cursor = self.conn.cursor()
        query = "SELECT * FROM properties WHERE 1=1"
        params = []

        if search:
            query += """ AND (
                title LIKE ? OR address LIKE ? OR city LIKE ? OR
                neighborhood LIKE ? OR owner_name LIKE ? OR owner_phone LIKE ?
            )"""
            s = f"%{search}%"
            params.extend([s, s, s, s, s, s])

        if filters:
            if filters.get("property_type") and filters["property_type"] != "همه":
                query += " AND property_type=?"
                params.append(filters["property_type"])
            if filters.get("deal_type") and filters["deal_type"] != "همه":
                query += " AND deal_type=?"
                params.append(filters["deal_type"])
            if filters.get("status") and filters["status"] != "همه":
                query += " AND status=?"
                params.append(filters["status"])
            if filters.get("city") and filters["city"].strip():
                query += " AND city LIKE ?"
                params.append(f"%{filters['city']}%")

        query += " ORDER BY id DESC"
        cursor.execute(query, params)
        return cursor.fetchall()

    def get_by_id(self, prop_id):
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM properties WHERE id=?", (prop_id,))
        return cursor.fetchone()

    def close(self):
        self.conn.close()


class PropertyForm(ctk.CTkToplevel):
    def __init__(self, parent, db, prop_id=None, on_save=None):
        super().__init__(parent)
        self.db = db
        self.prop_id = prop_id
        self.on_save = on_save
        self.title("افزودن / ویرایش ملک" if not prop_id else "ویرایش ملک")
        self.geometry("700x750")
        self.resizable(False, False)
        self.transient(parent)
        self.grab_set()

        self.create_widgets()
        if prop_id:
            self.load_data()

    def create_widgets(self):
        main = ctk.CTkScrollableFrame(self)
        main.pack(fill="both", expand=True, padx=15, pady=15)

        # عنوان
        ctk.CTkLabel(main, text="عنوان ملک *", font=("", 13, "bold")).grid(row=0, column=0, sticky="e", pady=5, padx=5)
        self.title_entry = ctk.CTkEntry(main, width=400, placeholder_text="مثال: آپارتمان ۱۰۰ متری نیاوران")
        self.title_entry.grid(row=0, column=1, columnspan=3, sticky="w", pady=5)

        # نوع ملک و نوع معامله
        ctk.CTkLabel(main, text="نوع ملک", font=("", 13)).grid(row=1, column=0, sticky="e", pady=5, padx=5)
        self.prop_type = ctk.CTkComboBox(main, values=["آپارتمان", "ویلا", "خانه", "مغازه", "دفتر", "زمین", "باغ", "سایر"], width=180)
        self.prop_type.set("آپارتمان")
        self.prop_type.grid(row=1, column=1, sticky="w", pady=5)

        ctk.CTkLabel(main, text="نوع معامله", font=("", 13)).grid(row=1, column=2, sticky="e", pady=5, padx=5)
        self.deal_type = ctk.CTkComboBox(main, values=["فروش", "اجاره", "رهن", "رهن و اجاره", "مشارکت"], width=150)
        self.deal_type.set("فروش")
        self.deal_type.grid(row=1, column=3, sticky="w", pady=5)

        # قیمت و متراژ
        ctk.CTkLabel(main, text="قیمت (تومان)", font=("", 13)).grid(row=2, column=0, sticky="e", pady=5, padx=5)
        self.price_entry = ctk.CTkEntry(main, width=180, placeholder_text="مثال: 15000000000")
        self.price_entry.grid(row=2, column=1, sticky="w", pady=5)

        ctk.CTkLabel(main, text="متراژ (متر)", font=("", 13)).grid(row=2, column=2, sticky="e", pady=5, padx=5)
        self.area_entry = ctk.CTkEntry(main, width=150, placeholder_text="مثال: 120")
        self.area_entry.grid(row=2, column=3, sticky="w", pady=5)

        # اتاق و طبقه
        ctk.CTkLabel(main, text="تعداد اتاق", font=("", 13)).grid(row=3, column=0, sticky="e", pady=5, padx=5)
        self.rooms_entry = ctk.CTkEntry(main, width=180, placeholder_text="مثال: 3")
        self.rooms_entry.grid(row=3, column=1, sticky="w", pady=5)

        ctk.CTkLabel(main, text="طبقه", font=("", 13)).grid(row=3, column=2, sticky="e", pady=5, padx=5)
        self.floor_entry = ctk.CTkEntry(main, width=150, placeholder_text="مثال: ۳ از ۵")
        self.floor_entry.grid(row=3, column=3, sticky="w", pady=5)

        # سال ساخت و وضعیت
        ctk.CTkLabel(main, text="سال ساخت", font=("", 13)).grid(row=4, column=0, sticky="e", pady=5, padx=5)
        self.year_entry = ctk.CTkEntry(main, width=180, placeholder_text="مثال: 1400")
        self.year_entry.grid(row=4, column=1, sticky="w", pady=5)

        ctk.CTkLabel(main, text="وضعیت", font=("", 13)).grid(row=4, column=2, sticky="e", pady=5, padx=5)
        self.status = ctk.CTkComboBox(main, values=["فعال", "فروخته شد", "اجاره رفت", "معلق", "آرشیو"], width=150)
        self.status.set("فعال")
        self.status.grid(row=4, column=3, sticky="w", pady=5)

        # شهر و محله
        ctk.CTkLabel(main, text="شهر", font=("", 13)).grid(row=5, column=0, sticky="e", pady=5, padx=5)
        self.city_entry = ctk.CTkEntry(main, width=180, placeholder_text="مثال: تهران")
        self.city_entry.grid(row=5, column=1, sticky="w", pady=5)

        ctk.CTkLabel(main, text="محله", font=("", 13)).grid(row=5, column=2, sticky="e", pady=5, padx=5)
        self.neighborhood_entry = ctk.CTkEntry(main, width=150, placeholder_text="مثال: نیاوران")
        self.neighborhood_entry.grid(row=5, column=3, sticky="w", pady=5)

        # آدرس
        ctk.CTkLabel(main, text="آدرس کامل", font=("", 13)).grid(row=6, column=0, sticky="ne", pady=5, padx=5)
        self.address_entry = ctk.CTkTextbox(main, width=400, height=60)
        self.address_entry.grid(row=6, column=1, columnspan=3, sticky="w", pady=5)

        # مالک
        ctk.CTkLabel(main, text="نام مالک / معرف", font=("", 13)).grid(row=7, column=0, sticky="e", pady=5, padx=5)
        self.owner_entry = ctk.CTkEntry(main, width=180)
        self.owner_entry.grid(row=7, column=1, sticky="w", pady=5)

        ctk.CTkLabel(main, text="تلفن", font=("", 13)).grid(row=7, column=2, sticky="e", pady=5, padx=5)
        self.phone_entry = ctk.CTkEntry(main, width=150, placeholder_text="09...")
        self.phone_entry.grid(row=7, column=3, sticky="w", pady=5)

        # توضیحات
        ctk.CTkLabel(main, text="توضیحات", font=("", 13)).grid(row=8, column=0, sticky="ne", pady=5, padx=5)
        self.desc_entry = ctk.CTkTextbox(main, width=400, height=100)
        self.desc_entry.grid(row=8, column=1, columnspan=3, sticky="w", pady=5)

        # دکمه‌ها
        btn_frame = ctk.CTkFrame(main, fg_color="transparent")
        btn_frame.grid(row=9, column=0, columnspan=4, pady=20)

        ctk.CTkButton(btn_frame, text="ذخیره", width=140, height=40, command=self.save,
                      font=("", 14, "bold")).pack(side="right", padx=10)
        ctk.CTkButton(btn_frame, text="انصراف", width=120, height=40, fg_color="gray",
                      command=self.destroy).pack(side="right", padx=10)

    def load_data(self):
        row = self.db.get_by_id(self.prop_id)
        if not row:
            return
        self.title_entry.insert(0, row[1] or "")
        self.prop_type.set(row[2] or "آپارتمان")
        self.deal_type.set(row[3] or "فروش")
        self.price_entry.insert(0, str(int(row[4])) if row[4] else "")
        self.area_entry.insert(0, str(row[5]) if row[5] else "")
        self.rooms_entry.insert(0, str(row[6]) if row[6] else "")
        self.floor_entry.insert(0, row[7] or "")
        self.year_entry.insert(0, str(row[8]) if row[8] else "")
        self.address_entry.insert("1.0", row[9] or "")
        self.city_entry.insert(0, row[10] or "")
        self.neighborhood_entry.insert(0, row[11] or "")
        self.status.set(row[12] or "فعال")
        self.owner_entry.insert(0, row[13] or "")
        self.phone_entry.insert(0, row[14] or "")
        self.desc_entry.insert("1.0", row[15] or "")

    def get_data(self):
        try:
            price = float(self.price_entry.get().replace(",", "").strip() or 0)
        except ValueError:
            price = 0
        try:
            area = float(self.area_entry.get().strip() or 0)
        except ValueError:
            area = 0
        try:
            rooms = int(self.rooms_entry.get().strip() or 0)
        except ValueError:
            rooms = 0
        try:
            year = int(self.year_entry.get().strip() or 0)
        except ValueError:
            year = 0

        return {
            "title": self.title_entry.get().strip(),
            "property_type": self.prop_type.get(),
            "deal_type": self.deal_type.get(),
            "price": price,
            "area": area,
            "rooms": rooms,
            "floor": self.floor_entry.get().strip(),
            "year_built": year,
            "address": self.address_entry.get("1.0", "end").strip(),
            "city": self.city_entry.get().strip(),
            "neighborhood": self.neighborhood_entry.get().strip(),
            "status": self.status.get(),
            "owner_name": self.owner_entry.get().strip(),
            "owner_phone": self.phone_entry.get().strip(),
            "description": self.desc_entry.get("1.0", "end").strip(),
        }

    def save(self):
        data = self.get_data()
        if not data["title"]:
            messagebox.showwarning("هشدار", "عنوان ملک الزامی است.")
            return
        try:
            if self.prop_id:
                self.db.update_property(self.prop_id, data)
                messagebox.showinfo("موفق", "ملک با موفقیت ویرایش شد.")
            else:
                self.db.add_property(data)
                messagebox.showinfo("موفق", "ملک جدید با موفقیت ثبت شد.")
            if self.on_save:
                self.on_save()
            self.destroy()
        except Exception as e:
            messagebox.showerror("خطا", f"خطا در ذخیره: {e}")


class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("نرم‌افزار فایلینگ املاک")
        self.geometry("1200x700")
        self.minsize(1000, 600)

        self.db = Database()
        self.selected_id = None

        self.create_ui()
        self.refresh_table()

    def create_ui(self):
        # هدر
        header = ctk.CTkFrame(self, height=60, corner_radius=0)
        header.pack(fill="x")
        header.pack_propagate(False)

        ctk.CTkLabel(header, text="🏠  نرم‌افزار فایلینگ املاک", font=("", 20, "bold")).pack(side="right", padx=20, pady=15)
        ctk.CTkLabel(header, text="مدیریت فایل‌های ملکی", font=("", 12), text_color="gray").pack(side="right", padx=5)

        # نوار ابزار
        toolbar = ctk.CTkFrame(self)
        toolbar.pack(fill="x", padx=10, pady=8)

        ctk.CTkButton(toolbar, text="➕ افزودن ملک", width=130, command=self.add_property,
                      font=("", 13, "bold")).pack(side="right", padx=5)
        ctk.CTkButton(toolbar, text="✏️ ویرایش", width=100, command=self.edit_property).pack(side="right", padx=5)
        ctk.CTkButton(toolbar, text="🗑️ حذف", width=90, fg_color="#c0392b", hover_color="#a93226",
                      command=self.delete_property).pack(side="right", padx=5)
        ctk.CTkButton(toolbar, text="📄 خروجی Excel", width=120, fg_color="#27ae60", hover_color="#1e8449",
                      command=self.export_csv).pack(side="right", padx=5)

        # فیلترها
        filter_frame = ctk.CTkFrame(self)
        filter_frame.pack(fill="x", padx=10, pady=5)

        ctk.CTkLabel(filter_frame, text="جستجو:").pack(side="right", padx=5)
        self.search_entry = ctk.CTkEntry(filter_frame, width=200, placeholder_text="عنوان، آدرس، مالک، تلفن...")
        self.search_entry.pack(side="right", padx=5)
        self.search_entry.bind("<Return>", lambda e: self.refresh_table())

        ctk.CTkLabel(filter_frame, text="نوع ملک:").pack(side="right", padx=(15, 5))
        self.filter_type = ctk.CTkComboBox(filter_frame, values=["همه", "آپارتمان", "ویلا", "خانه", "مغازه", "دفتر", "زمین", "باغ", "سایر"], width=110)
        self.filter_type.set("همه")
        self.filter_type.pack(side="right", padx=5)

        ctk.CTkLabel(filter_frame, text="معامله:").pack(side="right", padx=(15, 5))
        self.filter_deal = ctk.CTkComboBox(filter_frame, values=["همه", "فروش", "اجاره", "رهن", "رهن و اجاره", "مشارکت"], width=110)
        self.filter_deal.set("همه")
        self.filter_deal.pack(side="right", padx=5)

        ctk.CTkLabel(filter_frame, text="وضعیت:").pack(side="right", padx=(15, 5))
        self.filter_status = ctk.CTkComboBox(filter_frame, values=["همه", "فعال", "فروخته شد", "اجاره رفت", "معلق", "آرشیو"], width=110)
        self.filter_status.set("همه")
        self.filter_status.pack(side="right", padx=5)

        ctk.CTkButton(filter_frame, text="اعمال فیلتر", width=100, command=self.refresh_table).pack(side="right", padx=10)
        ctk.CTkButton(filter_frame, text="پاک کردن", width=80, fg_color="gray", command=self.clear_filters).pack(side="right", padx=5)

        # جدول
        table_frame = ctk.CTkFrame(self)
        table_frame.pack(fill="both", expand=True, padx=10, pady=5)

        style = ttk.Style()
        style.theme_use("clam")
        style.configure("Treeview", font=("", 11), rowheight=28)
        style.configure("Treeview.Heading", font=("", 11, "bold"))

        columns = ("id", "title", "type", "deal", "price", "area", "rooms", "city", "status", "owner", "phone")
        self.tree = ttk.Treeview(table_frame, columns=columns, show="headings", selectmode="browse")

        headings = {
            "id": ("کد", 50),
            "title": ("عنوان", 200),
            "type": ("نوع", 80),
            "deal": ("معامله", 80),
            "price": ("قیمت", 120),
            "area": ("متراژ", 70),
            "rooms": ("اتاق", 50),
            "city": ("شهر / محله", 120),
            "status": ("وضعیت", 80),
            "owner": ("مالک", 100),
            "phone": ("تلفن", 110),
        }

        for col, (text, width) in headings.items():
            self.tree.heading(col, text=text)
            self.tree.column(col, width=width, anchor="center")

        scrollbar = ttk.Scrollbar(table_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        self.tree.pack(side="right", fill="both", expand=True)
        scrollbar.pack(side="left", fill="y")

        self.tree.bind("<Double-1>", lambda e: self.edit_property())
        self.tree.bind("<<TreeviewSelect>>", self.on_select)

        # نوار وضعیت
        self.status_bar = ctk.CTkLabel(self, text="آماده", anchor="e", font=("", 11))
        self.status_bar.pack(fill="x", padx=10, pady=5)

    def format_price(self, price):
        if not price:
            return "-"
        try:
            p = int(float(price))
            return f"{p:,}"
        except:
            return str(price)

    def refresh_table(self):
        for item in self.tree.get_children():
            self.tree.delete(item)

        filters = {
            "property_type": self.filter_type.get(),
            "deal_type": self.filter_deal.get(),
            "status": self.filter_status.get(),
        }
        search = self.search_entry.get().strip()
        rows = self.db.get_all(search=search, filters=filters)

        for row in rows:
            city_neigh = f"{row[10] or ''} / {row[11] or ''}".strip(" /")
            self.tree.insert("", "end", values=(
                row[0],
                row[1],
                row[2],
                row[3],
                self.format_price(row[4]),
                row[5] or "-",
                row[6] or "-",
                city_neigh,
                row[12],
                row[13] or "-",
                row[14] or "-",
            ))

        self.status_bar.configure(text=f"تعداد فایل‌ها: {len(rows)}")

    def clear_filters(self):
        self.search_entry.delete(0, "end")
        self.filter_type.set("همه")
        self.filter_deal.set("همه")
        self.filter_status.set("همه")
        self.refresh_table()

    def on_select(self, event):
        selected = self.tree.selection()
        if selected:
            item = self.tree.item(selected[0])
            self.selected_id = item["values"][0]
        else:
            self.selected_id = None

    def add_property(self):
        PropertyForm(self, self.db, on_save=self.refresh_table)

    def edit_property(self):
        if not self.selected_id:
            messagebox.showwarning("هشدار", "لطفاً یک ملک را از جدول انتخاب کنید.")
            return
        PropertyForm(self, self.db, prop_id=self.selected_id, on_save=self.refresh_table)

    def delete_property(self):
        if not self.selected_id:
            messagebox.showwarning("هشدار", "لطفاً یک ملک را از جدول انتخاب کنید.")
            return
        if messagebox.askyesno("تأیید حذف", f"آیا از حذف ملک با کد {self.selected_id} مطمئن هستید؟"):
            self.db.delete_property(self.selected_id)
            self.selected_id = None
            self.refresh_table()
            messagebox.showinfo("موفق", "ملک حذف شد.")

    def export_csv(self):
        path = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
            initialfile=f"amlak_export_{datetime.now().strftime('%Y%m%d')}.csv"
        )
        if not path:
            return
        rows = self.db.get_all()
        try:
            with open(path, "w", newline="", encoding="utf-8-sig") as f:
                writer = csv.writer(f)
                writer.writerow([
                    "کد", "عنوان", "نوع ملک", "نوع معامله", "قیمت", "متراژ", "اتاق",
                    "طبقه", "سال ساخت", "آدرس", "شهر", "محله", "وضعیت",
                    "مالک", "تلفن", "توضیحات", "تاریخ ثبت", "آخرین ویرایش"
                ])
                for row in rows:
                    writer.writerow(row)
            messagebox.showinfo("موفق", f"خروجی با موفقیت ذخیره شد:\n{path}")
        except Exception as e:
            messagebox.showerror("خطا", f"خطا در خروجی گرفتن: {e}")

    def on_closing(self):
        self.db.close()
        self.destroy()


if __name__ == "__main__":
    app = App()
    app.protocol("WM_DELETE_WINDOW", app.on_closing)
    app.mainloop()
