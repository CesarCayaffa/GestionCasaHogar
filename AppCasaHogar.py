import sqlite3
import tkinter as tk
from tkinter import ttk, messagebox
from tkcalendar import DateEntry
from datetime import datetime
from PIL import Image, ImageTk

def conectar_db():
    conn = sqlite3.connect("gestion.db")
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS ingresos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            paciente TEXT NOT NULL,
            fecha TEXT NOT NULL,
            forma_pago TEXT NOT NULL,
            descripcion TEXT,
            monto REAL NOT NULL,
            pagado INTEGER DEFAULT 0
        )
    """)
    # Migración segura: asegurar columna 'descripcion' en ingresos si la DB ya existía sin ella
    try:
        c.execute("PRAGMA table_info(ingresos)")
        columnas = [row[1] for row in c.fetchall()]
        if 'descripcion' not in columnas:
            c.execute("ALTER TABLE ingresos ADD COLUMN descripcion TEXT")
    except sqlite3.Error:
        pass
    c.execute("""
        CREATE TABLE IF NOT EXISTS egresos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            fecha TEXT NOT NULL,
            descripcion TEXT NOT NULL,
            categoria TEXT NOT NULL,
            factura TEXT,
            monto REAL NOT NULL
        )
    """)
    c.execute("""
        CREATE TABLE IF NOT EXISTS residentes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT NOT NULL,
            fecha_nacimiento TEXT NOT NULL,
            fecha_ingreso TEXT NOT NULL,
            tipo_plan TEXT NOT NULL,
            fecha_salida TEXT
        )
    """)
    c.execute("""
        CREATE TABLE IF NOT EXISTS medicamentos_residente (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            residente_id INTEGER NOT NULL,
            medicamento TEXT NOT NULL,
            dosis TEXT,
            cantidad TEXT NOT NULL,
            fecha_adquisicion TEXT NOT NULL,
            fecha_vencimiento TEXT NOT NULL,
            FOREIGN KEY (residente_id) REFERENCES residentes (id) ON DELETE CASCADE
        )
    """)
    c.execute("""
        CREATE TABLE IF NOT EXISTS empleados (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT NOT NULL,
            fecha_ingreso TEXT NOT NULL,
            fecha_nacimiento TEXT,
            sueldo_hora REAL NOT NULL
        )
    """)
    c.execute("""
        CREATE TABLE IF NOT EXISTS asistencia_empleados (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            empleado_id INTEGER NOT NULL,
            fecha TEXT NOT NULL,
            FOREIGN KEY (empleado_id) REFERENCES empleados (id) ON DELETE CASCADE
        )
    """)
    conn.commit()
    conn.close()

def obtener_fecha_formato(date_entry):
    return date_entry.get_date().strftime("%Y-%m-%d")

# INGRESOS

def agregar_ingreso():
    conn = sqlite3.connect("gestion.db")
    c = conn.cursor()
    c.execute("INSERT INTO ingresos (paciente, fecha, forma_pago, descripcion, monto, pagado) VALUES (?, ?, ?, ?, ?, ?)",
              (entry_paciente.get(), obtener_fecha_formato(entry_fecha_ingreso), entry_forma_pago.get(), entry_descripcion_ingreso.get(), float(entry_monto_ingreso.get()), var_pagado.get()))
    conn.commit()
    conn.close()
    entry_paciente.delete(0, tk.END)
    entry_forma_pago.delete(0, tk.END)
    entry_descripcion_ingreso.delete(0, tk.END)
    entry_monto_ingreso.delete(0, tk.END)
    var_pagado.set(0)
    actualizar_listas()

def cargar_ingreso(event):
    selected_item = tree_ingresos.selection()[0]
    values = tree_ingresos.item(selected_item, 'values')
    entry_paciente.delete(0, tk.END)
    entry_paciente.insert(0, values[1])
    entry_fecha_ingreso.set_date(datetime.strptime(values[2], "%Y-%m-%d"))
    entry_forma_pago.delete(0, tk.END)
    entry_forma_pago.insert(0, values[3])
    entry_monto_ingreso.delete(0, tk.END)
    # Descripción ahora viene en la tabla (columna 4)
    entry_descripcion_ingreso.delete(0, tk.END)
    try:
        entry_descripcion_ingreso.insert(0, values[4] or "")
    except Exception:
        entry_descripcion_ingreso.insert(0, "")
    # Monto y pagado se desplazan un índice por la nueva columna
    entry_monto_ingreso.insert(0, values[5])
    var_pagado.set(1 if values[6] == "Sí" else 0)
    btn_actualizar_ingreso.config(state=tk.NORMAL)
    btn_agregar_ingreso.config(state=tk.DISABLED)
    btn_eliminar_ingreso.config(state=tk.NORMAL)

def actualizar_ingreso():
    selected_item = tree_ingresos.selection()[0]
    ingreso_id = tree_ingresos.item(selected_item, 'values')[0]
    conn = sqlite3.connect("gestion.db")
    c = conn.cursor()
    c.execute("UPDATE ingresos SET paciente = ?, fecha = ?, forma_pago = ?, descripcion = ?, monto = ?, pagado = ? WHERE id = ?",
              (entry_paciente.get(), obtener_fecha_formato(entry_fecha_ingreso), entry_forma_pago.get(), entry_descripcion_ingreso.get(), float(entry_monto_ingreso.get()), var_pagado.get(), ingreso_id))
    conn.commit()
    conn.close()
    entry_paciente.delete(0, tk.END)
    entry_forma_pago.delete(0, tk.END)
    entry_descripcion_ingreso.delete(0, tk.END)
    entry_monto_ingreso.delete(0, tk.END)
    var_pagado.set(0)
    btn_actualizar_ingreso.config(state=tk.DISABLED)
    btn_agregar_ingreso.config(state=tk.NORMAL)
    actualizar_listas()

def eliminar_ingreso():
    selected_item = tree_ingresos.selection()[0]
    ingreso_id = tree_ingresos.item(selected_item, 'values')[0]
    conn = sqlite3.connect("gestion.db")
    c = conn.cursor()
    c.execute("DELETE FROM ingresos WHERE id = ?", (ingreso_id,))
    conn.commit()
    conn.close()
    entry_paciente.delete(0, tk.END)
    entry_forma_pago.delete(0, tk.END)
    entry_descripcion_ingreso.delete(0, tk.END)
    entry_monto_ingreso.delete(0, tk.END)
    btn_eliminar_ingreso.config(state=tk.DISABLED)
    btn_actualizar_ingreso.config(state=tk.DISABLED)
    btn_agregar_ingreso.config(state=tk.NORMAL)
    actualizar_listas()

def cancelar_actualizacion_ingreso():
    entry_paciente.delete(0, tk.END)
    entry_forma_pago.delete(0, tk.END)
    entry_descripcion_ingreso.delete(0, tk.END)
    entry_monto_ingreso.delete(0, tk.END)
    var_pagado.set(0)
    btn_actualizar_ingreso.config(state=tk.DISABLED)
    btn_agregar_ingreso.config(state=tk.NORMAL)
    btn_eliminar_ingreso.config(state=tk.DISABLED)

def validar_ingreso():
    if not entry_paciente.get() or not entry_forma_pago.get() or not entry_monto_ingreso.get():
        messagebox.showerror("Error", "Todos los campos son obligatorios.")
        return False
    return True

# EGRESOS

def agregar_egreso():
    conn = sqlite3.connect("gestion.db")
    c = conn.cursor()
    c.execute("INSERT INTO egresos (fecha, descripcion, categoria, factura, monto) VALUES (?, ?, ?, ?, ?)",
              (obtener_fecha_formato(entry_fecha_egreso), entry_descripcion.get(), entry_categoria.get(), entry_factura.get(), float(entry_monto_egreso.get())))
    conn.commit()
    conn.close()
    entry_descripcion.delete(0, tk.END)
    entry_categoria.delete(0, tk.END)
    entry_factura.delete(0, tk.END)
    entry_monto_egreso.delete(0, tk.END)
    actualizar_listas()

def cargar_egreso(event):
    selected_item = tree_egresos.selection()[0]
    values = tree_egresos.item(selected_item, 'values')
    entry_fecha_egreso.set_date(datetime.strptime(values[1], "%Y-%m-%d"))
    entry_descripcion.delete(0, tk.END)
    entry_descripcion.insert(0, values[2])
    entry_categoria.delete(0, tk.END)
    entry_categoria.insert(0, values[3])
    entry_factura.delete(0, tk.END)
    entry_factura.insert(0, values[4])
    entry_monto_egreso.delete(0, tk.END)
    entry_monto_egreso.insert(0, values[5])
    btn_actualizar_egreso.config(state=tk.NORMAL)
    btn_agregar_egreso.config(state=tk.DISABLED)
    btn_eliminar_egreso.config(state=tk.NORMAL)
    
def actualizar_egreso():
    selected_item = tree_egresos.selection()[0]
    egreso_id = tree_egresos.item(selected_item, 'values')[0]
    conn = sqlite3.connect("gestion.db")
    c = conn.cursor()
    c.execute("UPDATE egresos SET fecha = ?, descripcion = ?, categoria = ?, factura = ?, monto = ? WHERE id = ?",
                (obtener_fecha_formato(entry_fecha_egreso), entry_descripcion.get(), entry_categoria.get(), entry_factura.get(), float(entry_monto_egreso.get()), egreso_id))
    conn.commit()
    conn.close()
    entry_descripcion.delete(0, tk.END)
    entry_categoria.delete(0, tk.END)
    entry_factura.delete(0, tk.END)
    entry_monto_egreso.delete(0, tk.END)
    btn_actualizar_egreso.config(state=tk.DISABLED)
    btn_agregar_egreso.config(state=tk.NORMAL)
    btn_eliminar_egreso.config(state=tk.DISABLED)
    actualizar_listas()

def eliminar_egreso():
    selected_item = tree_egresos.selection()[0]
    egreso_id = tree_egresos.item(selected_item, 'values')[0]
    conn = sqlite3.connect("gestion.db")
    c = conn.cursor()
    c.execute("DELETE FROM egresos WHERE id = ?", (egreso_id,))
    conn.commit()
    conn.close()
    entry_descripcion.delete(0, tk.END)
    entry_categoria.delete(0, tk.END)
    entry_factura.delete(0, tk.END)
    entry_monto_egreso.delete(0, tk.END)
    btn_eliminar_egreso.config(state=tk.DISABLED)
    btn_actualizar_egreso.config(state=tk.DISABLED)
    btn_agregar_egreso.config(state=tk.NORMAL)
    actualizar_listas()

def cancelar_actualizacion_egreso():
    entry_descripcion.delete(0, tk.END)
    entry_categoria.delete(0, tk.END)
    entry_factura.delete(0, tk.END)
    entry_monto_egreso.delete(0, tk.END)
    btn_actualizar_egreso.config(state=tk.DISABLED)
    btn_agregar_egreso.config(state=tk.NORMAL)
    btn_eliminar_egreso.config(state=tk.DISABLED)

def validar_egreso():
    if not entry_fecha_egreso.get() or not entry_descripcion.get() or not entry_categoria.get() or not entry_monto_egreso.get():
        messagebox.showerror("Error", "Todos los campos son obligatorios.")
        return False
    return True

# CALCULOS

def calcular_balance():
    conn = sqlite3.connect("gestion.db")
    c = conn.cursor()
    c.execute("SELECT SUM(monto) FROM ingresos WHERE strftime('%m', fecha) = ? AND strftime('%Y', fecha) = ?", (combo_mes.get(), combo_anio.get()))
    total_ingresos = c.fetchone()[0] or 0
    c.execute("SELECT SUM(monto) FROM egresos WHERE strftime('%m', fecha) = ? AND strftime('%Y', fecha) = ?", (combo_mes.get(), combo_anio.get()))
    total_egresos = c.fetchone()[0] or 0
    saldo = total_ingresos - total_egresos
    conn.close()
    label_balance.config(text=f"Balance General: {saldo:.2f} $.")

def calcular_total_restante():
    conn = sqlite3.connect("gestion.db")
    c = conn.cursor()
    c.execute("SELECT SUM(monto) FROM ingresos")
    total_ingresos = c.fetchone()[0] or 0
    c.execute("SELECT SUM(monto) FROM egresos")
    total_egresos = c.fetchone()[0] or 0
    saldo = total_ingresos - total_egresos
    conn.close()
    label_restante.config(text=f"Vienen: {saldo:.2f} $.")

def calcular_ingresos_mesuales():
    conn = sqlite3.connect("gestion.db")
    c = conn.cursor()
    c.execute("SELECT SUM(monto) FROM ingresos WHERE strftime('%m', fecha) = ? AND strftime('%Y', fecha) = ? AND pagado = 1", (combo_mes.get(), combo_anio.get()))
    total_ingresos = c.fetchone()[0] or 0
    conn.close()
    label_ingresos_mesuales.config(text=f"Ingresos Mensuales: {total_ingresos:.2f} $.")

def calcular_egresos_mesuales():
    conn = sqlite3.connect("gestion.db")
    c = conn.cursor()
    c.execute("SELECT SUM(monto) FROM egresos WHERE strftime('%m', fecha) = ? AND strftime('%Y', fecha) = ?", (combo_mes.get(), combo_anio.get()))
    total_egresos = c.fetchone()[0] or 0
    conn.close()
    label_egresos_mesuales.config(text=f"Egresos Mensuales: {total_egresos:.2f} $.")

def calcular_egresos_categoria_mensuales(categoria):
    conn = sqlite3.connect("gestion.db")
    c = conn.cursor()
    c.execute("SELECT SUM(monto) FROM egresos WHERE categoria = ? AND strftime('%m', fecha) = ? AND strftime('%Y', fecha) = ?", (categoria, combo_mes.get(), combo_anio.get()))
    total_categoria = c.fetchone()[0] or 0
    conn.close()
    return total_categoria

def actualizar_categoria_labels():
    label_categoria_comida.config(text=f"Comida: {calcular_egresos_categoria_mensuales('COMIDA'):.2f} $.")
    label_categoria_mtto.config(text=f"Mantenimiento: {calcular_egresos_categoria_mensuales('MTTO'):.2f} $.")
    label_categoria_insumos.config(text=f"Insumos: {calcular_egresos_categoria_mensuales('INSUMOS'):.2f} $.")
    label_categoria_limpieza.config(text=f"Limpieza: {calcular_egresos_categoria_mensuales('LIMPIEZA'):.2f} $.")
    label_categoria_empleados.config(text=f"Empleados: {calcular_egresos_categoria_mensuales('EMPLEADOS'):.2f} $.")
    label_categoria_extras.config(text=f"Extras: {calcular_egresos_categoria_mensuales('EXTRAS'):.2f} $.")
    label_categoria_fijos.config(text=f"Fijos: {calcular_egresos_categoria_mensuales('FIJOS'):.2f} $.")
    label_categoria_abono.config(text=f"Abono a Deuda: {calcular_egresos_categoria_mensuales('ABONO A DEUDA'):.2f} $.")

# RESIDENTES

def agregar_residente():
    conn = sqlite3.connect("gestion.db")
    c = conn.cursor()
    c.execute("INSERT INTO residentes (nombre, fecha_nacimiento, fecha_ingreso, tipo_plan) VALUES (?, ?, ?, ?)",
                (entry_nombre_residente.get(), obtener_fecha_formato(entry_fecha_nacimiento), obtener_fecha_formato(entry_fecha_ingreso_residente), entry_tipo_plan.get()))
    conn.commit()
    conn.close()
    entry_nombre_residente.delete(0, tk.END)
    entry_fecha_nacimiento.set_date(datetime.now())
    entry_fecha_ingreso_residente.set_date(datetime.now())
    entry_tipo_plan.delete(0, tk.END)
    actualizar_listas()

def cargar_residente(event):
    selected_item = tree_residentes.selection()[0]
    values = tree_residentes.item(selected_item, 'values')
    entry_nombre_residente.delete(0, tk.END)
    entry_nombre_residente.insert(0, values[1])
    entry_fecha_nacimiento.set_date(datetime.strptime(values[2], "%Y-%m-%d"))
    entry_fecha_ingreso_residente.set_date(datetime.strptime(values[3], "%Y-%m-%d"))
    entry_tipo_plan.delete(0, tk.END)
    entry_tipo_plan.insert(0, values[4])
    btn_actualizar_residente.config(state=tk.NORMAL)
    btn_agregar_residente.config(state=tk.DISABLED)
    btn_eliminar_residente.config(state=tk.NORMAL)

def eliminar_residente():
    selected_item = tree_residentes.selection()[0]
    residente_id = tree_residentes.item(selected_item, 'values')[0]
    conn = sqlite3.connect("gestion.db")
    c = conn.cursor()
    c.execute("DELETE FROM residentes WHERE id = ?", (residente_id,))
    conn.commit()
    conn.close()
    entry_nombre_residente.delete(0, tk.END)
    entry_fecha_nacimiento.set_date(datetime.now())
    entry_fecha_ingreso_residente.set_date(datetime.now())
    entry_tipo_plan.delete(0, tk.END)
    btn_eliminar_residente.config(state=tk.DISABLED)
    btn_actualizar_residente.config(state=tk.DISABLED)
    btn_agregar_residente.config(state=tk.NORMAL)
    actualizar_listas()

def actualizar_residente():
    selected_item = tree_residentes.selection()[0]
    residente_id = tree_residentes.item(selected_item, 'values')[0]
    conn = sqlite3.connect("gestion.db")
    c = conn.cursor()
    c.execute("UPDATE residentes SET nombre = ?, fecha_nacimiento = ?, fecha_ingreso = ?, tipo_plan = ? WHERE id = ?",
                (entry_nombre_residente.get(), obtener_fecha_formato(entry_fecha_nacimiento), obtener_fecha_formato(entry_fecha_ingreso_residente), entry_tipo_plan.get(), residente_id))
    conn.commit()
    conn.close()
    entry_nombre_residente.delete(0, tk.END)
    entry_fecha_nacimiento.set_date(datetime.now())
    entry_fecha_ingreso_residente.set_date(datetime.now())
    entry_tipo_plan.delete(0, tk.END)
    btn_actualizar_residente.config(state=tk.DISABLED)
    btn_agregar_residente.config(state=tk.NORMAL)
    btn_eliminar_residente.config(state=tk.DISABLED)
    actualizar_listas()

def cancelar_actualizacion_residente():
    entry_nombre_residente.delete(0, tk.END)
    entry_fecha_nacimiento.set_date(datetime.now())
    entry_fecha_ingreso_residente.set_date(datetime.now())
    entry_tipo_plan.delete(0, tk.END)
    btn_actualizar_residente.config(state=tk.DISABLED)
    btn_agregar_residente.config(state=tk.NORMAL)
    btn_eliminar_residente.config(state=tk.DISABLED)

def validar_residente():
    if not entry_nombre_residente.get() or not entry_fecha_nacimiento.get() or not entry_fecha_ingreso_residente.get():
        messagebox.showerror("Error", "Todos los campos son obligatorios.")
        return False
    return True

# MEDICAMENTOS

def cargar_nombres_residentes():
    conn = sqlite3.connect("gestion.db")
    c = conn.cursor()
    c.execute("SELECT nombre FROM residentes ORDER BY nombre")
    nombres = [row[0] for row in c.fetchall()]
    conn.close()
    entry_buscar_residente['values'] = nombres
    entry_paciente['values'] = nombres

def buscar_residente():
    conn = sqlite3.connect("gestion.db")
    c = conn.cursor()
    c.execute("SELECT id FROM residentes WHERE nombre = ?", (entry_buscar_residente.get(),))
    residente_id = c.fetchone()
    if residente_id:
        residente_id = residente_id[0]
        cargar_medicamentos(residente_id)
    conn.close()

def cargar_medicamentos(residente_id):
    tree_medicamentos.delete(*tree_medicamentos.get_children())
    conn = sqlite3.connect("gestion.db")
    c = conn.cursor()
    c.execute("SELECT id, medicamento, dosis, cantidad, fecha_adquisicion, fecha_vencimiento FROM medicamentos_residente WHERE residente_id = ?", (residente_id,))
    for row in c.fetchall():
        tree_medicamentos.insert("", "end", values=row)
    conn.close()

def cargar_medicamento(event):
    selected_item = tree_medicamentos.selection()[0]
    values = tree_medicamentos.item(selected_item, 'values')
    entry_nombre_medicamento.delete(0, tk.END)
    entry_nombre_medicamento.insert(0, values[1])
    entry_dosis.delete(0, tk.END)
    entry_dosis.insert(0, values[2])
    entry_cantidad.delete(0, tk.END)
    entry_cantidad.insert(0, values[3])
    entry_fecha_adquisicion.set_date(datetime.strptime(values[4], "%Y-%m-%d"))
    entry_fecha_vencimiento.set_date(datetime.strptime(values[5], "%Y-%m-%d"))
    btn_actualizar_medicamento.config(state=tk.NORMAL)
    btn_agregar_medicamento.config(state=tk.DISABLED)
    btn_eliminar_medicamento.config(state=tk.NORMAL)

def agregar_medicamento():
    conn = sqlite3.connect("gestion.db")
    c = conn.cursor()
    c.execute("SELECT id FROM residentes WHERE nombre = ?", (entry_buscar_residente.get(),))
    residente_id = c.fetchone()[0]
    c.execute("INSERT INTO medicamentos_residente (residente_id, medicamento, dosis, cantidad, fecha_adquisicion, fecha_vencimiento) VALUES (?, ?, ?, ?, ?, ?)",
              (residente_id, entry_nombre_medicamento.get(), entry_dosis.get(), entry_cantidad.get(), obtener_fecha_formato(entry_fecha_adquisicion), obtener_fecha_formato(entry_fecha_vencimiento)))
    conn.commit()
    conn.close()
    entry_nombre_medicamento.delete(0, tk.END)
    entry_dosis.delete(0, tk.END)
    entry_cantidad.delete(0, tk.END)
    entry_fecha_adquisicion.set_date(datetime.now())
    entry_fecha_vencimiento.set_date(datetime.now())
    cargar_medicamentos(residente_id)

def eliminar_medicamento():
    selected_item = tree_medicamentos.selection()[0]
    medicamento_id = tree_medicamentos.item(selected_item, 'values')[0]
    conn = sqlite3.connect("gestion.db")
    c = conn.cursor()
    c.execute("DELETE FROM medicamentos_residente WHERE id = ?", (medicamento_id,))
    conn.commit()
    conn.close()
    entry_nombre_medicamento.delete(0, tk.END)
    entry_dosis.delete(0, tk.END)
    entry_cantidad.delete(0, tk.END)
    entry_fecha_adquisicion.set_date(datetime.now())
    entry_fecha_vencimiento.set_date(datetime.now())
    btn_eliminar_medicamento.config(state=tk.DISABLED)
    btn_actualizar_medicamento.config(state=tk.DISABLED)
    btn_agregar_medicamento.config(state=tk.NORMAL)
    buscar_residente()

def actualizar_medicamento():
    selected_item = tree_medicamentos.selection()[0]
    medicamento_id = tree_medicamentos.item(selected_item, 'values')[0]
    conn = sqlite3.connect("gestion.db")
    c = conn.cursor()
    c.execute("UPDATE medicamentos_residente SET medicamento = ?, dosis = ?, cantidad = ?, fecha_adquisicion = ?, fecha_vencimiento = ? WHERE id = ?",
              (entry_nombre_medicamento.get(), entry_dosis.get(), entry_cantidad.get(), obtener_fecha_formato(entry_fecha_adquisicion), obtener_fecha_formato(entry_fecha_vencimiento), medicamento_id))
    conn.commit()
    conn.close()
    entry_nombre_medicamento.delete(0, tk.END)
    entry_dosis.delete(0, tk.END)
    entry_cantidad.delete(0, tk.END)
    entry_fecha_adquisicion.set_date(datetime.now())
    entry_fecha_vencimiento.set_date(datetime.now())
    btn_actualizar_medicamento.config(state=tk.DISABLED)
    btn_agregar_medicamento.config(state=tk.NORMAL)
    btn_eliminar_medicamento.config(state=tk.DISABLED)
    buscar_residente()

def cancelar_actualizacion_medicamento():
    entry_nombre_medicamento.delete(0, tk.END)
    entry_dosis.delete(0, tk.END)
    entry_cantidad.delete(0, tk.END)
    entry_fecha_adquisicion.set_date(datetime.now())
    entry_fecha_vencimiento.set_date(datetime.now())
    btn_actualizar_medicamento.config(state=tk.DISABLED)
    btn_agregar_medicamento.config(state=tk.NORMAL)
    btn_eliminar_medicamento.config(state=tk.DISABLED)

def validar_medicamento():
    if not entry_buscar_residente.get():
        messagebox.showerror("Error", "Debe seleccionar un residente.")
        return False
    if not entry_nombre_medicamento.get() or not entry_cantidad.get() or not entry_fecha_adquisicion.get() or not entry_fecha_vencimiento.get():
        messagebox.showerror("Error", "Todos los campos son obligatorios.")
        return False
    return True

# EMPLEADOS

def agregar_empleado():
    conn = sqlite3.connect("gestion.db")
    c = conn.cursor()
    c.execute("INSERT INTO empleados (nombre, fecha_ingreso, fecha_nacimiento, sueldo_hora) VALUES (?, ?, ?, ?)",
                (entry_nombre_empleado.get(), obtener_fecha_formato(entry_fecha_ingreso_empleado), obtener_fecha_formato(entry_fecha_nacimiento_empleado), float(entry_salario.get())))
    conn.commit()
    conn.close()
    entry_nombre_empleado.delete(0, tk.END)
    entry_fecha_ingreso_empleado.set_date(datetime.now())
    entry_fecha_nacimiento_empleado.set_date(datetime.now())
    entry_salario.delete(0, tk.END)
    actualizar_listas()

def cargar_empleado(event):
    selected_item = tree_empleados.selection()[0]
    values = tree_empleados.item(selected_item, 'values')
    entry_nombre_empleado.delete(0, tk.END)
    entry_nombre_empleado.insert(0, values[1])
    entry_fecha_ingreso_empleado.set_date(datetime.strptime(values[2], "%Y-%m-%d"))
    entry_fecha_nacimiento_empleado.set_date(datetime.strptime(values[3], "%Y-%m-%d"))
    entry_salario.delete(0, tk.END)
    entry_salario.insert(0, values[4])
    btn_actualizar_empleado.config(state=tk.NORMAL)
    btn_agregar_empleado.config(state=tk.DISABLED)
    btn_eliminar_empleado.config(state=tk.NORMAL)

def eliminar_empleado():
    selected_item = tree_empleados.selection()[0]
    empleado_id = tree_empleados.item(selected_item, 'values')[0]
    conn = sqlite3.connect("gestion.db")
    c = conn.cursor()
    c.execute("DELETE FROM empleados WHERE id = ?", (empleado_id,))
    conn.commit()
    conn.close()
    entry_nombre_empleado.delete(0, tk.END)
    entry_fecha_ingreso_empleado.set_date(datetime.now())
    entry_fecha_nacimiento_empleado.set_date(datetime.now())
    entry_salario.delete(0, tk.END)
    btn_eliminar_empleado.config(state=tk.DISABLED)
    btn_actualizar_empleado.config(state=tk.DISABLED)
    btn_agregar_empleado.config(state=tk.NORMAL)
    actualizar_listas()

def actualizar_empleado():
    selected_item = tree_empleados.selection()[0]
    empleado_id = tree_empleados.item(selected_item, 'values')[0]
    conn = sqlite3.connect("gestion.db")
    c = conn.cursor()
    c.execute("UPDATE empleados SET nombre = ?, fecha_ingreso = ?, fecha_nacimiento = ?, sueldo_hora = ? WHERE id = ?",
                (entry_nombre_empleado.get(), obtener_fecha_formato(entry_fecha_ingreso_empleado), obtener_fecha_formato(entry_fecha_nacimiento_empleado), float(entry_salario.get()), empleado_id))
    conn.commit()
    conn.close()
    entry_nombre_empleado.delete(0, tk.END)
    entry_fecha_ingreso_empleado.set_date(datetime.now())
    entry_fecha_nacimiento_empleado.set_date(datetime.now())
    entry_salario.delete(0, tk.END)
    btn_actualizar_empleado.config(state=tk.DISABLED)
    btn_agregar_empleado.config(state=tk.NORMAL)
    btn_eliminar_empleado.config(state=tk.DISABLED)
    actualizar_listas()

def cancelar_actualizacion_empleado():
    entry_nombre_empleado.delete(0, tk.END)
    entry_fecha_ingreso_empleado.set_date(datetime.now())
    entry_fecha_nacimiento_empleado.set_date(datetime.now())
    entry_salario.delete(0, tk.END)
    btn_actualizar_empleado.config(state=tk.DISABLED)
    btn_agregar_empleado.config(state=tk.NORMAL)
    btn_eliminar_empleado.config(state=tk.DISABLED)

def validar_empleado():
    if not entry_nombre_empleado.get() or not entry_fecha_ingreso_empleado.get() or not entry_fecha_nacimiento_empleado.get() or not entry_salario.get():
        messagebox.showerror("Error", "Todos los campos son obligatorios.")
        return False
    return True
 
# ASISTENCIA EMPLEADOS

def cargar_nombres_empleados():
    conn = sqlite3.connect("gestion.db")
    c = conn.cursor()
    # Verificar si la tabla empleados existe
    c.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='empleados'")
    if c.fetchone() is None:
        conn.close()
        return []
    c.execute("SELECT id, nombre FROM empleados ORDER BY nombre")
    empleados = c.fetchall()
    conn.close()
    return empleados

def mostrar_checkboxes():
    # Eliminar los checkboxes existentes
    for widget in frame_asistencia_empleado.grid_slaves():
        if isinstance(widget, ttk.Checkbutton):
            widget.destroy()

    empleados = cargar_nombres_empleados()
    max_columns = 2  # Número máximo de columnas para distribuir los checkboxes

    for i, (emp_id, emp_nombre) in enumerate(empleados):
        var = tk.BooleanVar()
        chk = ttk.Checkbutton(frame_asistencia_empleado, text=emp_nombre, variable=var)
        row = i // max_columns + 3  # Empezar una fila más abajo
        column = i % max_columns
        if column == 0:
            chk.grid(row=row, column=column, sticky="e", padx=5, pady=2)
        else:
            chk.grid(row=row, column=column, sticky="w", padx=5, pady=2)
        checkboxes[emp_id] = var

def registrar_asistencia():
    fecha = entry_fecha_asistencia_empleado.get()

    empleados_asistentes = [emp_id for emp_id, var in checkboxes.items() if var.get()]


    conn = None
    try:
        conn = sqlite3.connect("gestion.db")
        c = conn.cursor()
        for emp_id in empleados_asistentes:
            c.execute("SELECT COUNT(*) FROM asistencia_empleados WHERE empleado_id = ? AND fecha = ?", (emp_id, fecha))
            if c.fetchone()[0] == 0:
                c.execute("INSERT INTO asistencia_empleados (empleado_id, fecha) VALUES (?, ?)", (emp_id, fecha))
        conn.commit()
        messagebox.showinfo("Éxito", "Asistencia registrada correctamente.")
    except sqlite3.Error as e:
        messagebox.showerror("Error", f"Error al registrar la asistencia: {e}")
    finally:
        if conn:
            conn.close()
            buscar_asistencia()
    for var in checkboxes.values():
        var.set(False)

    calcular_asistencia_quincenal(combo_mes.get(), combo_anio.get())

def buscar_asistencia():
    fecha = entry_fecha_asistencia_empleado.get()
    tree_asistencia.delete(*tree_asistencia.get_children())

    conn = sqlite3.connect("gestion.db")
    c = conn.cursor()
    c.execute("""
        SELECT asistencia_empleados.id, empleados.nombre, asistencia_empleados.fecha
        FROM asistencia_empleados
        JOIN empleados ON asistencia_empleados.empleado_id = empleados.id
        WHERE asistencia_empleados.fecha = ?
    """, (fecha,))
    for row in c.fetchall():
        tree_asistencia.insert("", "end", values=row)
    conn.close()

    actualizar_listas()

def cargar_asistencia(event):
    selected_item = tree_asistencia.selection()[0]
    values = tree_asistencia.item(selected_item, 'values')
    btn_eliminar_asistencia.config(state=tk.NORMAL)
    btn_registrar_asistencia.config(state=tk.DISABLED)

def eliminar_asistencia():
    selected_item = tree_asistencia.selection()[0]
    asistencia_id = tree_asistencia.item(selected_item, 'values')[0]
    conn = sqlite3.connect("gestion.db")
    c = conn.cursor()
    c.execute("DELETE FROM asistencia_empleados WHERE id = ?", (asistencia_id,))
    conn.commit()
    conn.close()
    btn_eliminar_asistencia.config(state=tk.DISABLED)
    btn_registrar_asistencia.config(state=tk.NORMAL)
    buscar_asistencia()
    actualizar_listas()

def cancelar_eliminar_asistencia():
    btn_eliminar_asistencia.config(state=tk.DISABLED)
    btn_registrar_asistencia.config(state=tk.NORMAL)

# Calcular asistencia de empleados por mes

def calcular_asistencia_quincenal(mes, anio):
    conn = sqlite3.connect("gestion.db")
    c = conn.cursor()
    
    # Calcular asistencia para la primera quincena (1-15)
    c.execute("""
        SELECT empleados.nombre, COUNT(asistencia_empleados.id), empleados.sueldo_hora
        FROM asistencia_empleados
        JOIN empleados ON asistencia_empleados.empleado_id = empleados.id
        WHERE strftime('%d', asistencia_empleados.fecha) BETWEEN '01' AND '15'
        AND strftime('%m', asistencia_empleados.fecha) = ?
        AND strftime('%Y', asistencia_empleados.fecha) = ?
        GROUP BY empleados.nombre
    """, (mes, anio))
    asistencia_primera_quincena = c.fetchall()
    
    # Calcular asistencia para la segunda quincena (16-31)
    c.execute("""
        SELECT empleados.nombre, COUNT(asistencia_empleados.id), empleados.sueldo_hora
        FROM asistencia_empleados
        JOIN empleados ON asistencia_empleados.empleado_id = empleados.id
        WHERE strftime('%d', asistencia_empleados.fecha) BETWEEN '16' AND '31'
        AND strftime('%m', asistencia_empleados.fecha) = ?
        AND strftime('%Y', asistencia_empleados.fecha) = ?
        GROUP BY empleados.nombre
    """, (mes, anio))
    asistencia_segunda_quincena = c.fetchall()
    
    conn.close()
    
    return asistencia_primera_quincena, asistencia_segunda_quincena

def mostrar_asistencia_quincenal():
    mes = combo_mes.get()
    anio = combo_anio.get()
    asistencia_primera_quincena, asistencia_segunda_quincena = calcular_asistencia_quincenal(mes, anio)
    
    # Limpiar la tabla de resultados
    tree_asistencia_quincenal.delete(*tree_asistencia_quincenal.get_children())
    
    # Mostrar resultados de la primera quincena
    for row in asistencia_primera_quincena:
        nombre, dias_trabajados, sueldo_hora = row
        salario_quincenal = dias_trabajados * sueldo_hora
        tree_asistencia_quincenal.insert("", "end", values=(nombre, dias_trabajados, "Primera quincena", salario_quincenal))
    
    # Mostrar resultados de la segunda quincena
    for row in asistencia_segunda_quincena:
        nombre, dias_trabajados, sueldo_hora = row
        salario_quincenal = dias_trabajados * sueldo_hora
        tree_asistencia_quincenal.insert("", "end", values=(nombre, dias_trabajados, "Segunda quincena", salario_quincenal))

def ver_detalles_asistencia():
    selected_item = tree_asistencia_quincenal.selection()
    if not selected_item:
        messagebox.showwarning("Atención", "Seleccione un empleado para ver los detalles.")
        return

    empleado = tree_asistencia_quincenal.item(selected_item[0], 'values')[0]
    mes = combo_mes.get()
    anio = combo_anio.get()

    # Crear una nueva ventana
    detalles_ventana = tk.Toplevel(root)
    detalles_ventana.title(f"Detalles de Asistencia - {empleado}")
    detalles_ventana.iconphoto(False, logo_tk)
    detalles_ventana.geometry("400x300")

    # Crear una tabla para mostrar los detalles de la asistencia
    columns_detalles = ("Fecha",)
    tree_detalles = ttk.Treeview(detalles_ventana, columns=columns_detalles, show="headings")
    for col in columns_detalles:
        tree_detalles.heading(col, text=col)
    tree_detalles.pack(expand=True, fill="both")

    # Obtener los detalles de la asistencia del empleado
    conn = sqlite3.connect("gestion.db")
    c = conn.cursor()

    # Obtener asistencia de la primera quincena
    tree_detalles.insert("", "end", values=("1ra Quincena",))
    c.execute("""
        SELECT fecha
        FROM asistencia_empleados
        JOIN empleados ON asistencia_empleados.empleado_id = empleados.id
        WHERE empleados.nombre = ?
        AND strftime('%m', asistencia_empleados.fecha) = ?
        AND strftime('%Y', asistencia_empleados.fecha) = ?
        AND strftime('%d', asistencia_empleados.fecha) BETWEEN '01' AND '15'
        ORDER BY fecha
    """, (empleado, mes, anio))
    for row in c.fetchall():
        tree_detalles.insert("", "end", values=row)

    # Obtener asistencia de la segunda quincena
    tree_detalles.insert("", "end", values=("2da Quincena",))
    c.execute("""
        SELECT fecha
        FROM asistencia_empleados
        JOIN empleados ON asistencia_empleados.empleado_id = empleados.id
        WHERE empleados.nombre = ?
        AND strftime('%m', asistencia_empleados.fecha) = ?
        AND strftime('%Y', asistencia_empleados.fecha) = ?
        AND strftime('%d', asistencia_empleados.fecha) BETWEEN '16' AND '31'
        ORDER BY fecha
    """, (empleado, mes, anio))
    for row in c.fetchall():
        tree_detalles.insert("", "end", values=row)

    conn.close()

# RECORDATORIOS

def verificar_pagos_pendientes():
    conn = sqlite3.connect("gestion.db")
    c = conn.cursor()
    c.execute("SELECT id, paciente, fecha, monto FROM ingresos WHERE pagado = 0 ORDER BY fecha")
    pagos_pendientes = c.fetchall()
    conn.close()

    if pagos_pendientes:
        ventana_pagos_pendientes = tk.Toplevel(root)
        ventana_pagos_pendientes.title("Pagos Pendientes")        
        ventana_pagos_pendientes.iconphoto(False, logo_tk )

        columns = ("ID", "Residente", "Fecha", "Monto")
        tree_pagos_pendientes = ttk.Treeview(ventana_pagos_pendientes, columns=columns, show="headings")
        for col in columns:
            tree_pagos_pendientes.heading(col, text=col)
            tree_pagos_pendientes.column(col, stretch=tk.YES, anchor="center")

        tree_pagos_pendientes.column("ID", width=0, stretch=tk.NO)
        tree_pagos_pendientes.pack(expand=True, fill="both")

        for pago in pagos_pendientes:
            tree_pagos_pendientes.insert("", "end", values=(pago[0], pago[1], pago[2], pago[3]))

        def marcar_como_pagado():
            selected_item = tree_pagos_pendientes.selection()[0]
            pago_id = tree_pagos_pendientes.item(selected_item, 'values')[0]
            conn = sqlite3.connect("gestion.db")
            c = conn.cursor()
            c.execute("UPDATE ingresos SET pagado = 1 WHERE id = ?", (pago_id,))
            conn.commit()
            conn.close()
            tree_pagos_pendientes.delete(selected_item)
            messagebox.showinfo("Éxito", "Pago marcado como pagado.")
            actualizar_listas()

        btn_marcar_pagado = ttk.Button(ventana_pagos_pendientes, text="Marcar como Pagado", command=marcar_como_pagado)
        btn_marcar_pagado.pack(pady=10)
    else:
        messagebox.showinfo("Recordatorio", "No hay pagos pendientes.")

def verificar_medicamentos_vencidos():
    conn = sqlite3.connect("gestion.db")
    c = conn.cursor()
    c.execute("""
        SELECT residentes.nombre, medicamentos_residente.medicamento, medicamentos_residente.fecha_vencimiento 
        FROM medicamentos_residente 
        JOIN residentes ON medicamentos_residente.residente_id = residentes.id 
        WHERE medicamentos_residente.fecha_vencimiento < date('now')
    """)
    medicamentos_vencidos = c.fetchall()
    c.execute("""
        SELECT residentes.nombre, medicamentos_residente.medicamento, medicamentos_residente.fecha_vencimiento 
        FROM medicamentos_residente 
        JOIN residentes ON medicamentos_residente.residente_id = residentes.id 
        WHERE medicamentos_residente.fecha_vencimiento BETWEEN date('now') AND date('now', '+7 days')
    """)
    proximos_a_vencer = c.fetchall()
    conn.close()

    if medicamentos_vencidos or proximos_a_vencer:
        mensaje = ""
        if medicamentos_vencidos:
            mensaje += "MEDICAMENTOS VENCIDOS:\n\n"
            for nombre, medicamento, fecha_vencimiento in sorted(medicamentos_vencidos, key=lambda x: datetime.strptime(x[2], "%Y-%m-%d")):
                mensaje += f"Medicamento: {medicamento}, Fecha de vencimiento: {fecha_vencimiento},\nde {nombre} \n"
        if proximos_a_vencer:
            mensaje += "\nMEDICAMENTOS PRÓXIMOS A VENCER:\n\n"
            for nombre, medicamento, fecha_vencimiento in sorted(proximos_a_vencer, key=lambda x: datetime.strptime(x[2], "%Y-%m-%d")):
                mensaje += f"Medicamento: {medicamento}, Fecha de vencimiento: {fecha_vencimiento},\nde {nombre} \n"
        messagebox.showwarning("Recordatorio", mensaje)
    else:
        messagebox.showinfo("Recordatorio", "No hay medicamentos vencidos ni próximos a vencer.")

def verificar_cumples_mes():
    conn = sqlite3.connect("gestion.db")
    c = conn.cursor()
    c.execute("SELECT nombre, fecha_nacimiento FROM residentes WHERE strftime('%m', fecha_nacimiento) = ?", (combo_mes.get(),))
    cumpleaneros = c.fetchall()
    c.execute("SELECT nombre, fecha_nacimiento FROM empleados WHERE strftime('%m', fecha_nacimiento) = ?", (combo_mes.get(),))
    cumpleaneros += c.fetchall()
    conn.close()

    if cumpleaneros:
        cumpleaneros.sort(key=lambda x: datetime.strptime(x[1], "%Y-%m-%d").day)
        mensaje = "CUMPLEAÑOS ESTE MES:\n\n"
        for nombre, fecha_nacimiento in cumpleaneros:
            dia = datetime.strptime(fecha_nacimiento, "%Y-%m-%d").day
            mensaje += f"{nombre}, el Día: {dia}\n"
        messagebox.showinfo("Cumpleaños", mensaje)
    else:
        messagebox.showinfo("Cumpleaños", "No hay cumpleaños este mes.")

# ACTUALIZAR LISTAS

def actualizar_listas():
    tree_ingresos.delete(*tree_ingresos.get_children())
    tree_egresos.delete(*tree_egresos.get_children())
    tree_residentes.delete(*tree_residentes.get_children())
    tree_empleados.delete(*tree_empleados.get_children())
    
    conn = sqlite3.connect("gestion.db")
    c = conn.cursor()
    c.execute("SELECT id, paciente, fecha, forma_pago, descripcion, monto, pagado FROM ingresos WHERE strftime('%m', fecha) = ? AND strftime('%Y', fecha) = ? ORDER BY fecha", (combo_mes.get(), combo_anio.get()))
    for row in c.fetchall():
        pagado_str = "Sí" if row[6] == 1 else "No"
        tree_ingresos.insert("", "end", values=(row[0], row[1], row[2], row[3], row[4] or "", row[5], pagado_str))
    
    c.execute("SELECT id, fecha, descripcion, categoria, factura, monto FROM egresos WHERE strftime('%m', fecha) = ? AND strftime('%Y', fecha) = ? ORDER BY fecha", (combo_mes.get(), combo_anio.get()))
    for row in c.fetchall():
        tree_egresos.insert("", "end", values=row)

    c.execute("SELECT id, nombre, fecha_nacimiento, fecha_ingreso, tipo_plan, fecha_salida FROM residentes ORDER BY nombre")
    for row in c.fetchall():
        tree_residentes.insert("", "end", values=row)

    c.execute("SELECT id, nombre, fecha_ingreso, fecha_nacimiento, sueldo_hora FROM empleados ORDER BY nombre")
    for row in c.fetchall():
        tree_empleados.insert("", "end", values=row)
    
    conn.close()
    calcular_balance()
    calcular_ingresos_mesuales()
    calcular_egresos_mesuales()
    actualizar_categoria_labels()
    calcular_total_restante()
    cargar_nombres_residentes()
    mostrar_checkboxes()
    mostrar_asistencia_quincenal()



# Interfaz gráfica
root = tk.Tk()
root.title("CASA HOGAR")
root.state('zoomed')

# Configuración logo de la ventana
logo = Image.open("logo.png")
logo = logo.resize((32, 32), Image.Resampling.LANCZOS)
logo_tk = ImageTk.PhotoImage(logo)
root.iconphoto(False, logo_tk)

# Estilo
style = ttk.Style()
style.configure("TLabel", font=("Arial", 12))
style.configure("TButton", font=("Arial", 12))
style.configure("TEntry", font=("Arial", 12))
style.configure("TCombobox", font=("Arial", 12))
style.configure("Treeview.Heading", font=("Arial", 12, "bold"))
style.configure("Treeview", font=("Arial", 12))

notebook = ttk.Notebook(root)
frame_ingresos = ttk.Frame(notebook, padding="10 10 10 10")
frame_egresos = ttk.Frame(notebook, padding="10 10 10 10")
frame_balance = ttk.Frame(notebook, padding="10 10 10 10")
frame_principal = ttk.Frame(notebook, padding="10 10 10 10")
frame_residentes = ttk.Frame(notebook, padding="10 10 10 10")
frame_empleados = ttk.Frame(notebook, padding="10 10 10 10")
frame_inventario = ttk.Frame(notebook, padding="10 10 10 10")
frame_asistencia_empleado = ttk.Frame(notebook, padding="10 10 10 10")
notebook.add(frame_principal, text="Principal")
notebook.add(frame_residentes, text="Residentes")
notebook.add(frame_inventario, text="Inventario")
notebook.add(frame_empleados, text="Empleados")
notebook.add(frame_asistencia_empleado, text="Asistencia Empleados")
notebook.add(frame_ingresos, text="Ingresos")
notebook.add(frame_egresos, text="Egresos")
notebook.add(frame_balance, text="Balance")
notebook.pack(expand=True, fill="both")

# Configurar el contenedor para que las columnas se expandan
frame_ingresos.columnconfigure(0, weight=1)
frame_ingresos.columnconfigure(1, weight=1)

frame_ingresos.grid_rowconfigure(8, weight=1)

frame_egresos.columnconfigure(0, weight=1)
frame_egresos.columnconfigure(1, weight=1)

frame_egresos.grid_rowconfigure(7, weight=1)

frame_residentes.columnconfigure(0, weight=1)
frame_residentes.columnconfigure(1, weight=1)

frame_residentes.grid_rowconfigure(6, weight=1)

frame_inventario.columnconfigure(0, weight=1)
frame_inventario.columnconfigure(1, weight=1)

frame_inventario.grid_rowconfigure(9, weight=1)

frame_empleados.columnconfigure(0, weight=1)
frame_empleados.columnconfigure(1, weight=1)

frame_empleados.grid_rowconfigure(7, weight=1)

frame_asistencia_empleado.columnconfigure(0, weight=1)
frame_asistencia_empleado.columnconfigure(1, weight=1)


frame_asistencia_empleado.grid_rowconfigure(106, weight=1)
frame_asistencia_empleado.grid_rowconfigure(109, weight=1)


# Sección Principal
ttk.Label(frame_principal, text="Bienvenido a la Casa Hogar", font=("Arial", 16)).pack(pady=20)

imagen = Image.open("logo.png")
imagen = imagen.resize((300, 250), Image.Resampling.LANCZOS)
imagen_tk = ImageTk.PhotoImage(imagen)

label_imagen = ttk.Label(frame_principal, image=imagen_tk)
label_imagen.image = imagen_tk  
label_imagen.pack(pady=20)

# Agregar boton para ver recordatorios
btn_recordatorios = ttk.Button(frame_principal, text="Ver Pagos Pendientes", command=verificar_pagos_pendientes)
btn_recordatorios.pack(pady=10)

btn_recordatorios2 = ttk.Button(frame_principal, text="Ver Medicamentos Vencidos", command=verificar_medicamentos_vencidos)
btn_recordatorios2.pack(pady=10)

btn_recordatorios3 = ttk.Button(frame_principal, text="Ver Cumpleaños del Mes", command=verificar_cumples_mes)
btn_recordatorios3.pack(pady=10)

# Sección Ingresos
ttk.Label(frame_ingresos, text="Residente:").grid(row=0, column=0, padx=5, pady=5, sticky="e")
entry_paciente = ttk.Combobox(frame_ingresos)
entry_paciente.grid(row=0, column=1, padx=5, pady=5, sticky="w")

ttk.Label(frame_ingresos, text="Fecha").grid(row=1, column=0, padx=5, pady=5, sticky="e")
entry_fecha_ingreso = DateEntry(frame_ingresos, date_pattern="yyyy-mm-dd")
entry_fecha_ingreso.grid(row=1, column=1, padx=5, pady=5, sticky="w")

ttk.Label(frame_ingresos, text="Forma de Pago").grid(row=2, column=0, padx=5, pady=5, sticky="e")
entry_forma_pago = ttk.Combobox(frame_ingresos, values=["EFECTIVO", "BS", "ZELLE JUDITH", "ZELLE CESAR"])
entry_forma_pago.grid(row=2, column=1, padx=5, pady=5, sticky="w")

ttk.Label(frame_ingresos, text="Descripción").grid(row=3, column=0, padx=5, pady=5, sticky="e")
entry_descripcion_ingreso = ttk.Entry(frame_ingresos)
entry_descripcion_ingreso.grid(row=3, column=1, padx=5, pady=5, sticky="w")

ttk.Label(frame_ingresos, text="Monto").grid(row=4, column=0, padx=5, pady=5, sticky="e")
entry_monto_ingreso = ttk.Entry(frame_ingresos, validate="key", validatecommand=(root.register(lambda P: P.replace('.', '', 1).isdigit() or P == ""), '%P'))
entry_monto_ingreso.grid(row=4, column=1, padx=5, pady=5, sticky="w")

ttk.Label(frame_ingresos, text="Pagado").grid(row=5, column=0, padx=5, pady=5, sticky="e")
var_pagado = tk.IntVar()
check_pagado = ttk.Checkbutton(frame_ingresos, variable=var_pagado)
check_pagado.grid(row=5, column=1, padx=5, pady=5, sticky="w")

btn_agregar_ingreso = ttk.Button(frame_ingresos, text="Agregar Ingreso", command=lambda: agregar_ingreso() if validar_ingreso() else None, state=tk.ACTIVE)
btn_agregar_ingreso.grid(row=6, column=0, padx=5, pady=5, sticky="ew")

btn_eliminar_ingreso = ttk.Button(frame_ingresos, text="Eliminar Ingreso", command=eliminar_ingreso, state=tk.DISABLED)
btn_eliminar_ingreso.grid(row=6, column=1, padx=5, pady=5, sticky="ew")

btn_actualizar_ingreso = ttk.Button(frame_ingresos, text="Actualizar Ingreso", command=actualizar_ingreso, state=tk.DISABLED)
btn_actualizar_ingreso.grid(row=7, column=0, padx=5, pady=5, sticky="ew")

btn_cancelar_actualizacion = ttk.Button(frame_ingresos, text="Cancelar", command=cancelar_actualizacion_ingreso)
btn_cancelar_actualizacion.grid(row=7, column=1, padx=5, pady=5, sticky="ew")

columns = ("ID", "Residente", "Fecha", "Forma de Pago", "Descripción", "Monto", "Pagado")
tree_ingresos = ttk.Treeview(frame_ingresos, columns=columns, show="headings")
for col in columns:
    tree_ingresos.heading(col, text=col)
    tree_ingresos.column(col, stretch=tk.YES, anchor="center")

tree_ingresos.column("ID", width=0, stretch=tk.NO)
tree_ingresos.grid(row=8, column=0, columnspan=2, padx=5, pady=5, sticky="nsew")
tree_ingresos.bind("<Double-1>", cargar_ingreso)

# Mostrar Ingresos Mensuales
label_ingresos_mesuales = ttk.Label(frame_ingresos, text="Ingresos Mensuales: 0.00 $.")
label_ingresos_mesuales.grid(row=9, column=0, columnspan=2, padx=5, pady=5)

# Sección Egresos
ttk.Label(frame_egresos, text="Fecha").grid(row=0, column=0, padx=5, pady=5, sticky="e")
entry_fecha_egreso = DateEntry(frame_egresos, date_pattern="yyyy-mm-dd")
entry_fecha_egreso.grid(row=0, column=1, padx=5, pady=5, sticky="w")

ttk.Label(frame_egresos, text="Descripción").grid(row=1, column=0, padx=5, pady=5, sticky="e")
entry_descripcion = ttk.Entry(frame_egresos)
entry_descripcion.grid(row=1, column=1, padx=5, pady=5, sticky="w")

ttk.Label(frame_egresos, text="Categoría").grid(row=2, column=0, padx=5, pady=5, sticky="e")
entry_categoria = ttk.Combobox(frame_egresos, values=["COMIDA", "MTTO", "INSUMOS", "LIMPIEZA", "EMPLEADOS", "EXTRAS", "FIJOS", "ABONO A DEUDA"])
entry_categoria.grid(row=2, column=1, padx=5, pady=5, sticky="w")

ttk.Label(frame_egresos, text="Factura #").grid(row=3, column=0, padx=5, pady=5, sticky="e")
entry_factura = ttk.Entry(frame_egresos)
entry_factura.grid(row=3, column=1, padx=5, pady=5, sticky="w")

ttk.Label(frame_egresos, text="Monto").grid(row=4, column=0, padx=5, pady=5, sticky="e")
entry_monto_egreso = ttk.Entry(frame_egresos, validate="key", validatecommand=(root.register(lambda P: P.replace('.', '', 1).isdigit() or P == ""), '%P'))
entry_monto_egreso.grid(row=4, column=1, padx=5, pady=5, sticky="w")

btn_agregar_egreso = ttk.Button(frame_egresos, text="Agregar Egreso", command=lambda: agregar_egreso() if validar_egreso() else None)
btn_agregar_egreso.grid(row=5, column=0, padx=5, pady=5, sticky="ew")

btn_eliminar_egreso = ttk.Button(frame_egresos, text="Eliminar Egreso", command=eliminar_egreso, state=tk.DISABLED)
btn_eliminar_egreso.grid(row=5, column=1, padx=5, pady=5, sticky="ew")

btn_actualizar_egreso = ttk.Button(frame_egresos, text="Actualizar Egreso", command=actualizar_egreso, state=tk.DISABLED)
btn_actualizar_egreso.grid(row=6, column=0, padx=5, pady=5, sticky="ew")

btn_cancelar_actualizacion_egreso = ttk.Button(frame_egresos, text="Cancelar", command=cancelar_actualizacion_egreso)
btn_cancelar_actualizacion_egreso.grid(row=6, column=1, padx=5, pady=5, sticky="ew")

columns_egresos = ("ID", "Fecha", "Descripción", "Categoría", "Factura", "Monto")
tree_egresos = ttk.Treeview(frame_egresos, columns=columns_egresos, show="headings")
for col in columns_egresos:
    tree_egresos.heading(col, text=col)
    tree_egresos.column(col, stretch=tk.YES, anchor="center")

tree_egresos.column("ID", width=0, stretch=tk.NO)
tree_egresos.grid(row=7, column=0, columnspan=2, padx=5, pady=5, sticky="nsew")
tree_egresos.bind("<Double-1>", cargar_egreso)

# Mostrar Egresos Mensuales
label_egresos_mesuales = ttk.Label(frame_egresos, text="Egresos Mensuales: 0.00 $.")
label_egresos_mesuales.grid(row=8, column=0, columnspan=2, padx=5, pady=5)

# Balance
label_restante = ttk.Label(frame_balance, text="vienen: 0.00 $.")
label_restante.pack(padx=10, pady=10)
ttk.Label(frame_balance, text="RESUMEN DEL MES", font=("Arial", 12, "bold")).pack(padx=10, pady=10)
label_balance = ttk.Label(frame_balance, text="Balance General: 0.00 $.")
label_balance.pack(padx=10, pady=10)
ttk.Label(frame_balance, text="EGRESO POR CATEGORIA", font=("Arial", 12, "bold")).pack(padx=10, pady=10)
label_categoria_comida = ttk.Label(frame_balance, text="Comida: 0.00 $.")
label_categoria_comida.pack(padx=10, pady=10)
label_categoria_mtto = ttk.Label(frame_balance, text="Mantenimiento: 0.00 $.")
label_categoria_mtto.pack(padx=10, pady=10)
label_categoria_insumos = ttk.Label(frame_balance, text="Insumos: 0.00 $.")
label_categoria_insumos.pack(padx=10, pady=10)
label_categoria_limpieza = ttk.Label(frame_balance, text="Limpieza: 0.00 $.")
label_categoria_limpieza.pack(padx=10, pady=10)
label_categoria_empleados = ttk.Label(frame_balance, text="Empleados: 0.00 $.")
label_categoria_empleados.pack(padx=10, pady=10)
label_categoria_extras = ttk.Label(frame_balance, text="Extras: 0.00 $.")
label_categoria_extras.pack(padx=10, pady=10)
label_categoria_fijos = ttk.Label(frame_balance, text="Fijos: 0.00 $.")
label_categoria_fijos.pack(padx=10, pady=10)
label_categoria_abono = ttk.Label(frame_balance, text="Abono a Deuda: 0.00 $.")
label_categoria_abono.pack(padx=10, pady=10)

# Filtros de Mes y Año
# Colocar los filtros en la parte inferior y forzar tamaños más pequeños y readonly
filtros_frame = ttk.Frame(root, padding="6 6 6 6")
filtros_frame.pack(side=tk.BOTTOM, fill=tk.X)

ttk.Label(filtros_frame, text="Mes:").pack(side=tk.LEFT, padx=5, pady=3)
combo_mes = ttk.Combobox(filtros_frame, values=[f"{i:02d}" for i in range(1, 13)], width=5, state="readonly")
combo_mes.pack(side=tk.LEFT, padx=5, pady=3)
combo_mes.set(datetime.now().strftime("%m"))

ttk.Label(filtros_frame, text="Año:").pack(side=tk.LEFT, padx=5, pady=3)
combo_anio = ttk.Combobox(filtros_frame, values=[str(i) for i in range(2000, datetime.now().year + 1)], width=6, state="readonly")
combo_anio.pack(side=tk.LEFT, padx=5, pady=3)
combo_anio.set(datetime.now().strftime("%Y"))

# Botón actualizar - mantengo a la izquierda para que no ocupe espacio innecesario
ttk.Button(filtros_frame, text="Actualizar", command=actualizar_listas).pack(side=tk.LEFT, padx=5, pady=3)

# Vista de Residentes
ttk.Label(frame_residentes, text="Nombre").grid(row=0, column=0, padx=5, pady=5, sticky="e")
entry_nombre_residente = ttk.Entry(frame_residentes)
entry_nombre_residente.grid(row=0, column=1, padx=5, pady=5, sticky="w")

ttk.Label(frame_residentes, text="Fecha de Nacimiento").grid(row=1, column=0, padx=5, pady=5, sticky="e")
entry_fecha_nacimiento = DateEntry(frame_residentes, date_pattern="yyyy-mm-dd")
entry_fecha_nacimiento.grid(row=1, column=1, padx=5, pady=5, sticky="w")

ttk.Label(frame_residentes, text="Fecha de Ingreso").grid(row=2, column=0, padx=5, pady=5, sticky="e")
entry_fecha_ingreso_residente = DateEntry(frame_residentes, date_pattern="yyyy-mm-dd")
entry_fecha_ingreso_residente.grid(row=2, column=1, padx=5, pady=5, sticky="w")
ttk.Label(frame_residentes, text="Tipo de Plan").grid(row=3, column=0, padx=5, pady=5, sticky="e")

entry_tipo_plan = ttk.Combobox(frame_residentes, values=["Temporal", "Permanente", "Guardería"])
entry_tipo_plan.grid(row=3, column=1, padx=5, pady=5, sticky="w")

btn_agregar_residente = ttk.Button(frame_residentes, text="Agregar Residente", command=lambda: agregar_residente() if validar_residente() else None)
btn_agregar_residente.grid(row=4, column=0, padx=5, pady=5, sticky="ew")

btn_eliminar_residente = ttk.Button(frame_residentes, text="Eliminar Residente", command=eliminar_residente, state=tk.DISABLED)
btn_eliminar_residente.grid(row=4, column=1, padx=5, pady=5, sticky="ew")

btn_actualizar_residente = ttk.Button(frame_residentes, text="Actualizar Residente", command=actualizar_residente, state=tk.DISABLED)
btn_actualizar_residente.grid(row=5, column=0, padx=5, pady=5, sticky="ew")

btn_cancelar_actualizacion_residente = ttk.Button(frame_residentes, text="Cancelar", command=cancelar_actualizacion_residente)
btn_cancelar_actualizacion_residente.grid(row=5, column=1, padx=5, pady=5, sticky="ew")

columns_residentes = ("ID", "Nombre", "Fecha de Nacimiento", "Fecha de Ingreso", "Tipo de Plan", "Fecha de Salida")
tree_residentes = ttk.Treeview(frame_residentes, columns=columns_residentes, show="headings")
for col in columns_residentes:
    tree_residentes.heading(col, text=col)
    tree_residentes.column(col, stretch=tk.YES, anchor="center")
tree_residentes.column("ID", width=0, stretch=tk.NO)
tree_residentes.column("Fecha de Salida", width=0, stretch=tk.NO)
tree_residentes.grid(row=6, column=0, columnspan=2, padx=5, pady=5, sticky="nsew")
tree_residentes.bind("<Double-1>", cargar_residente)

# Vista inventario

ttk.Label(frame_inventario, text="Nombre del Residente").grid(row=0, column=0, padx=5, pady=5, sticky="e")
entry_buscar_residente= ttk.Combobox(frame_inventario)
entry_buscar_residente.grid(row=0, column=1, padx=5, pady=5, sticky="w")

btn_buscar_residente = ttk.Button(frame_inventario, text="Buscar", command=buscar_residente)
btn_buscar_residente.grid(row=1, column=1, padx=5, pady=5, sticky="ew")

ttk.Label(frame_inventario, text="Nombre del Medicamento").grid(row=2, column=0, padx=5, pady=5, sticky="e")  
entry_nombre_medicamento = ttk.Entry(frame_inventario)
entry_nombre_medicamento.grid(row=2, column=1, padx=5, pady=5, sticky="w")

ttk.Label(frame_inventario, text="Dosis por dia").grid(row=3, column=0, padx=5, pady=5, sticky="e")
entry_dosis = ttk.Entry(frame_inventario, validate="key", validatecommand=(root.register(lambda P: P.replace('.', '', 1).isdigit() or P == ""), '%P'))
entry_dosis.grid(row=3, column=1, padx=5, pady=5, sticky="w")

ttk.Label(frame_inventario, text="Cantidad").grid(row=4, column=0, padx=5, pady=5, sticky="e")
entry_cantidad = ttk.Entry(frame_inventario, validate="key", validatecommand=(root.register(lambda P: P.replace('.', '', 1).isdigit() or P == ""), '%P'))
entry_cantidad.grid(row=4, column=1, padx=5, pady=5, sticky="w")

ttk.Label(frame_inventario, text="Fecha de Adquisición").grid(row=5, column=0, padx=5, pady=5, sticky="e")
entry_fecha_adquisicion = DateEntry(frame_inventario, date_pattern="yyyy-mm-dd")
entry_fecha_adquisicion.grid(row=5, column=1, padx=5, pady=5, sticky="w")

ttk.Label(frame_inventario, text="Fecha de Vencimiento").grid(row=6, column=0, padx=5, pady=5, sticky="e")
entry_fecha_vencimiento = DateEntry(frame_inventario, date_pattern="yyyy-mm-dd")
entry_fecha_vencimiento.grid(row=6, column=1, padx=5, pady=5, sticky="w")

btn_agregar_medicamento = ttk.Button(frame_inventario, text="Agregar Medicamento", command=lambda: agregar_medicamento() if validar_medicamento() else None)
btn_agregar_medicamento.grid(row=7, column=0, padx=5, pady=5, sticky="ew")

btn_eliminar_medicamento = ttk.Button(frame_inventario, text="Eliminar Medicamento", command=eliminar_medicamento, state=tk.DISABLED)
btn_eliminar_medicamento.grid(row=7, column=1, padx=5, pady=5, sticky="ew")

btn_actualizar_medicamento = ttk.Button(frame_inventario, text="Actualizar Medicamento", command=actualizar_medicamento, state=tk.DISABLED)
btn_actualizar_medicamento.grid(row=8, column=0, padx=5, pady=5, sticky="ew")

btn_cancelar_actualizacion_medicamento = ttk.Button(frame_inventario, text="Cancelar", command=cancelar_actualizacion_medicamento)
btn_cancelar_actualizacion_medicamento.grid(row=8, column=1, padx=5, pady=5, sticky="ew")

columns_medicamentos = ("ID", "Nombre", "Dosis", "Cantidad", "Fecha de Adquisición", "Fecha de Vencimiento")
tree_medicamentos = ttk.Treeview(frame_inventario, columns=columns_medicamentos, show="headings")
for col in columns_medicamentos:
    tree_medicamentos.heading(col, text=col)
    tree_medicamentos.column(col, stretch=tk.YES, anchor="center")
tree_medicamentos.column("ID", width=0, stretch=tk.NO)
tree_medicamentos.grid(row=9, column=0, columnspan=2, padx=5, pady=5, sticky="nsew")
tree_medicamentos.bind("<Double-1>", cargar_medicamento)

# Vista Empleados

ttk.Label(frame_empleados, text="Nombre").grid(row=0, column=0, padx=5, pady=5, sticky="e")
entry_nombre_empleado = ttk.Entry(frame_empleados)
entry_nombre_empleado.grid(row=0, column=1, padx=5, pady=5, sticky="w")

ttk.Label(frame_empleados, text="Fecha de Nacimiento").grid(row=1, column=0, padx=5, pady=5, sticky="e")
entry_fecha_nacimiento_empleado = DateEntry(frame_empleados, date_pattern="yyyy-mm-dd")
entry_fecha_nacimiento_empleado.grid(row=1, column=1, padx=5, pady=5, sticky="w")

ttk.Label(frame_empleados, text="Fecha de Ingreso").grid(row=2, column=0, padx=5, pady=5, sticky="e")
entry_fecha_ingreso_empleado = DateEntry(frame_empleados, date_pattern="yyyy-mm-dd")
entry_fecha_ingreso_empleado.grid(row=2, column=1, padx=5, pady=5, sticky="w")


ttk.Label(frame_empleados, text="Salario por Guardia").grid(row=4, column=0, padx=5, pady=5, sticky="e")
entry_salario = ttk.Entry(frame_empleados, validate="key", validatecommand=(root.register(lambda P: P.replace('.', '', 1).isdigit() or P == ""), '%P'))
entry_salario.grid(row=4, column=1, padx=5, pady=5, sticky="w")

btn_agregar_empleado = ttk.Button(frame_empleados, text="Agregar Empleado", command=lambda: agregar_empleado() if validar_empleado() else None)
btn_agregar_empleado.grid(row=5, column=0, padx=5, pady=5, sticky="ew")

btn_eliminar_empleado = ttk.Button(frame_empleados, text="Eliminar Empleado", command=eliminar_empleado, state=tk.DISABLED)
btn_eliminar_empleado.grid(row=5, column=1, padx=5, pady=5, sticky="ew")

btn_actualizar_empleado = ttk.Button(frame_empleados, text="Actualizar Empleado", command=actualizar_empleado, state=tk.DISABLED)   
btn_actualizar_empleado.grid(row=6, column=0, padx=5, pady=5, sticky="ew")

btn_cancelar_actualizacion_empleado = ttk.Button(frame_empleados, text="Cancelar", command=cancelar_actualizacion_empleado)
btn_cancelar_actualizacion_empleado.grid(row=6, column=1, padx=5, pady=5, sticky="ew")

columns_empleados = ("ID", "Nombre", "Fecha de Ingreso", "Fecha de Nacimiento", "Salario por hora")
tree_empleados = ttk.Treeview(frame_empleados, columns=columns_empleados, show="headings")
for col in columns_empleados:
    tree_empleados.heading(col, text=col)
    tree_empleados.column(col, stretch=tk.YES, anchor="center")
tree_empleados.column("ID", width=0, stretch=tk.NO)
tree_empleados.grid(row=7, column=0, columnspan=2, padx=5, pady=5, sticky="nsew")
tree_empleados.bind("<Double-1>", cargar_empleado)

# Vista Asistencia Empleados
ttk.Label(frame_asistencia_empleado, text="Fecha").grid(row=0, column=0, padx=5, pady=5, sticky="e")
entry_fecha_asistencia_empleado = DateEntry(frame_asistencia_empleado, date_pattern="yyyy-mm-dd")
entry_fecha_asistencia_empleado.grid(row=0, column=1, padx=5, pady=5, sticky="w")

ttk.Label(frame_asistencia_empleado, text="Empleados que Trabajaron: ").grid(row=1, column=0, padx=5, pady=5, sticky="e")

checkboxes = {}
mostrar_checkboxes()

btn_registrar_asistencia = ttk.Button(frame_asistencia_empleado, text="Registrar Asistencia", command=registrar_asistencia)
btn_registrar_asistencia.grid(row=100, column=0, columnspan=2, padx=5, pady=5, sticky="ew")

btn_eliminar_asistencia = ttk.Button(frame_asistencia_empleado, text="Eliminar Asistencia", command=eliminar_asistencia, state=tk.DISABLED)
btn_eliminar_asistencia.grid(row=101, column=0, columnspan=2, padx=5, pady=5, sticky="ew")

btn_cancelar_asistencia = ttk.Button(frame_asistencia_empleado, text="Cancelar", command=cancelar_eliminar_asistencia)
btn_cancelar_asistencia.grid(row=102, column=0, columnspan=2, padx=5, pady=5, sticky="ew")

# Buscar asistencia

btn_buscar_asistencia = ttk.Button(frame_asistencia_empleado, text="Buscar", command=buscar_asistencia)
btn_buscar_asistencia.grid(row=105, column=0, columnspan=2, padx=5, pady=5, sticky="ew")

# tabla para mostrar los resultados de la busqueda
columns_asistencia = ("ID", "Empleado", "Fecha")
tree_asistencia = ttk.Treeview(frame_asistencia_empleado, columns=columns_asistencia, show="headings")
for col in columns_asistencia:
    tree_asistencia.heading(col, text=col)
    tree_asistencia.column(col, stretch=tk.YES, anchor="center")
tree_asistencia.column("ID", width=0, stretch=tk.NO)
tree_asistencia["height"] = 3
tree_asistencia.grid(row=106, column=0, columnspan=2, padx=5, pady=5, sticky="nsew")
tree_asistencia.bind("<Double-1>", cargar_asistencia)


# Agregar botón para calcular asistencia quincenal
btn_asistencia_quincenal = ttk.Button(frame_asistencia_empleado, text="Calcular Quincena", command=mostrar_asistencia_quincenal)
btn_asistencia_quincenal.grid(row=108, column=0, columnspan=2, padx=5, pady=5, sticky="ew")

# Tabla para mostrar los resultados de la asistencia quincenal
columns_asistencia_quincenal = ("Empleado", "Días Trabajados", "Quincena", "Salario Quincenal")
tree_asistencia_quincenal = ttk.Treeview(frame_asistencia_empleado, columns=columns_asistencia_quincenal, show="headings")
for col in columns_asistencia_quincenal:
    tree_asistencia_quincenal.heading(col, text=col)
    tree_asistencia_quincenal.column(col, stretch=tk.YES, anchor="center")
tree_asistencia_quincenal["height"] = 5
tree_asistencia_quincenal.grid(row=109, column=0, columnspan=2, padx=5, pady=5, sticky="nsew")

# Agregar botón para ver detalles de asistencia
btn_ver_detalles_asistencia = ttk.Button(frame_asistencia_empleado, text="Ver Detalles", command=ver_detalles_asistencia)
btn_ver_detalles_asistencia.grid(row=110, column=0, columnspan=2, padx=5, pady=5, sticky="ew")


# Inicializar la base de datos y cargar los datos
conectar_db()
actualizar_listas()
root.mainloop()