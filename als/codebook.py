"""ALSFRS-R item and level wording (English / Thai), word for word from the paper form."""

CODEBOOK = {
    'q1_Speech': {
        'no': 1, 'domain': 'bulbar', 'domain_th': 'กล้ามเนื้อในการพูดและการกลืน (bulbar)',
        'en': 'Speech', 'th': 'การพูด',
        'levels': {
            4: ('Normal', 'ปกติ'),
            3: ('Detectable speech disturbance', 'มีความผิดปกติของการพูดที่สังเกตได้'),
            2: ('Intelligible with repeating', 'เข้าใจได้เมื่อพูดซ้ำ'),
            1: ('Speech combined with nonvocal communication', 'ต้องใช้การสื่อสารแบบไม่ใช่การพูดร่วมด้วย'),
            0: ('Loss of useful speech', 'ไม่สามารถพูดให้เข้าใจได้'),
        },
    },
    'q2_Salivation': {
        'no': 2, 'domain': 'bulbar', 'domain_th': 'กล้ามเนื้อในการพูดและการกลืน (bulbar)',
        'en': 'Salivation', 'th': 'การหลั่งน้ำลาย (salivation)',
        'levels': {
            4: ('Normal', 'ปกติ'),
            3: ('Slight but definite excess of saliva in mouth; may have nighttime drooling', 'มีน้ำลายในปากมากเกินปกติเล็กน้อย อาจมีน้ำลายไหลยืดตอนกลางคืน'),
            2: ('Moderately excessive saliva; may have minimal drooling', 'มีน้ำลายในปากมากเกินระดับปานกลาง อาจมีน้ำลายไหลยืดเล็กน้อย'),
            1: ('Marked excess of saliva with some drooling', 'มีน้ำลายมากเกินอย่างชัดเจนและมีน้ำลายไหลยืด'),
            0: ('Marked drooling; requires constant tissue or handkerchief', 'มีน้ำลายไหลยืดอย่างชัดเจน ต้องใช้กระดาษเช็ดหน้า หรือผ้าเช็ดหน้าตลอดเวลา'),
        },
    },
    'q3_Swallowing': {
        'no': 3, 'domain': 'bulbar', 'domain_th': 'กล้ามเนื้อในการพูดและการกลืน (bulbar)',
        'en': 'Swallowing', 'th': 'การกลืน',
        'levels': {
            4: ('Normal', 'ปกติ'),
            3: ('Early eating problems — occasional choking', 'มีปัญหาในการกลืนระยะต้น — สำลักเป็นครั้งคราว'),
            2: ('Dietary consistency changes', 'ต้องเปลี่ยนเนื้อสัมผัสของอาหาร (dietary consistency)'),
            1: ('Needs supplemental tube feeding', 'ต้องใช้สายให้อาหารเสริม (supplemental tube feeding)'),
            0: ('NPO (exclusively parenteral or enteral feeding)', 'งดอาหารทางปาก (ให้อาหารทางหลอดเลือดดำหรือสายยางเท่านั้น)'),
        },
    },
    'q4_Handwriting': {
        'no': 4, 'domain': 'fine_motor', 'domain_th': 'กล้ามเนื้อมัดเล็ก (fine motor)',
        'en': 'Handwriting', 'th': 'การเขียน',
        'levels': {
            4: ('Normal', 'ปกติ'),
            3: ('Slow or sloppy; all words are legible', 'ช้าหรือไม่เรียบร้อย แต่อ่านออกทั้งหมด'),
            2: ('Not all words are legible', 'อ่านไม่ออกบางคำ'),
            1: ('Able to grip pen but unable to write', 'จับปากกาได้ แต่เขียนไม่ได้'),
            0: ('Unable to grip pen', 'ไม่สามารถจับปากกาได้'),
        },
    },
    'q5_Cutting_Food': {
        'no': 5, 'domain': 'fine_motor', 'domain_th': 'กล้ามเนื้อมัดเล็ก (fine motor)',
        'en': 'Cutting Food', 'th': 'การตัดแบ่งอาหาร',
        'levels': {
            4: ('Normal', 'ปกติ'),
            3: ('Somewhat slow and clumsy, but no help needed', 'ช้าและงุ่มง่ามเล็กน้อย แต่ไม่ต้องได้รับความช่วยเหลือ'),
            2: ('Can cut most foods, although clumsy and slow; some help needed', 'สามารถตัดอาหารส่วนใหญ่ได้ แต่งุ่มง่ามและช้า ต้องการความช่วยเหลือบ้าง'),
            1: ('Food must be cut by someone, but can still feed slowly', 'ต้องมีผู้อื่นตัดอาหารให้ แต่สามารถป้อนตัวเองได้ช้าๆ'),
            0: ('Needs to be fed', 'ต้องมีผู้อื่นป้อนอาหาร'),
        },
    },
    'q6_Dressing_and_Hygiene': {
        'no': 6, 'domain': 'fine_motor', 'domain_th': 'กล้ามเนื้อมัดเล็ก (fine motor)',
        'en': 'Dressing and Hygiene', 'th': 'การแต่งตัวและสุขอนามัย',
        'levels': {
            4: ('Normal', 'ปกติ'),
            3: ('Independent and complete self-care with effort or decreased efficiency', 'ดูแลตนเองได้อย่างอิสระและครบถ้วน แต่ต้องใช้ความพยายามหรือมีประสิทธิภาพลดลง'),
            2: ('Intermittent assistance or substitute methods', 'ต้องการความช่วยเหลือเป็นครั้งคราว หรือใช้วิธีอื่นทดแทน'),
            1: ('Needs attendant for self-care', 'ต้องมีผู้ดูแลคอยช่วยเหลือในการดูแลตนเอง'),
            0: ('Total dependence', 'ต้องพึ่งพาผู้ดูแลทั้งหมด'),
        },
    },
    'q7_Turning_in_Bed': {
        'no': 7, 'domain': 'gross_motor', 'domain_th': 'กล้ามเนื้อมัดใหญ่ (gross motor)',
        'en': 'Turning in Bed', 'th': 'การพลิกตัวบนเตียง',
        'levels': {
            4: ('Normal', 'ปกติ'),
            3: ('Somewhat slow and clumsy, but no help needed', 'ช้าและงุ่มง่ามเล็กน้อย แต่ไม่ต้องการความช่วยเหลือ'),
            2: ('Can turn alone or adjust sheets, but with great difficulty', 'สามารถพลิกตัวเองหรือจัดผ้าปูที่นอนได้ แต่ลำบากมาก'),
            1: ('Can initiate, but not turn or adjust sheets alone', 'สามารถเริ่มการพลิกตัวได้ แต่ไม่สามารถพลิกตัวหรือจัดผ้าปูที่นอนเองได้'),
            0: ('Helpless', 'ช่วยเหลือตัวเองไม่ได้'),
        },
    },
    'q8_Walking': {
        'no': 8, 'domain': 'gross_motor', 'domain_th': 'กล้ามเนื้อมัดใหญ่ (gross motor)',
        'en': 'Walking', 'th': 'การเดิน',
        'levels': {
            4: ('Normal', 'ปกติ'),
            3: ('Early ambulation difficulties', 'มีปัญหาการเดินในระยะต้น'),
            2: ('Walks with assistance', 'เดินได้โดยต้องมีผู้ช่วยเหลือ'),
            1: ('Non-ambulatory functional movement only', 'เคลื่อนไหวขาได้ แต่เดินไม่ได้'),
            0: ('No purposeful leg movement', 'ไม่สามารถเคลื่อนไหวขาตามจุดประสงค์'),
        },
    },
    'q9_Climbing_Stairs': {
        'no': 9, 'domain': 'gross_motor', 'domain_th': 'กล้ามเนื้อมัดใหญ่ (gross motor)',
        'en': 'Climbing Stairs', 'th': 'การขึ้นบันได',
        'levels': {
            4: ('Normal', 'ปกติ'),
            3: ('Slow', 'ช้า'),
            2: ('Mild unsteadiness or fatigue', 'ไม่มั่นคงหรือเหนื่อยล้าเล็กน้อย'),
            1: ('Needs assistance', 'ต้องการความช่วยเหลือ'),
            0: ('Cannot do', 'ขึ้นบันไดไม่ได้'),
        },
    },
    'q10_Dyspnea': {
        'no': 10, 'domain': 'respiratory', 'domain_th': 'การหายใจ (respiratory)',
        'en': 'Dyspnea', 'th': 'ภาวะหายใจลำบาก (dyspnea)',
        'levels': {
            4: ('None', 'ไม่มี'),
            3: ('Occurs when walking', 'เกิดขึ้นเมื่อเดิน'),
            2: ('Occurs with one or more of the following: eating, bathing, dressing (ADL)', 'เกิดขึ้นเมื่อทำกิจวัตรประจำวันต่อไปนี้ อย่างน้อยหนึ่งอย่าง: การกิน อาบน้ำ แต่งตัว (ADL)'),
            1: ('Occurs at rest, difficulty breathing when either sitting or lying', 'เกิดขึ้นขณะพัก หายใจลำบากเมื่อนั่งหรือนอน'),
            0: ('Significant difficulty, considering using mechanical respiratory support', 'หายใจลำบากมาก มีการพิจารณาใช้เครื่องช่วยหายใจ'),
        },
    },
    'q11_Orthopnea': {
        'no': 11, 'domain': 'respiratory', 'domain_th': 'การหายใจ (respiratory)',
        'en': 'Orthopnea', 'th': 'ภาวะหายใจลำบากเมื่อนอนราบ (orthopnea)',
        'levels': {
            4: ('None', 'ไม่มี'),
            3: ('Some difficulty sleeping at night due to shortness of breath. Does not routinely use more than two pillows', 'มีปัญหาการนอนในตอนกลางคืนเนื่องจากหายใจไม่สะดวก ไม่จำเป็นต้องใช้หมอนมากกว่าสองใบ'),
            2: ('Needs extra pillow in order to sleep (more than two)', 'ต้องใช้หมอนเพิ่ม (มากกว่าสองใบ)'),
            1: ('Can only sleep sitting up', 'นอนได้เฉพาะในท่านั่ง'),
            0: ('Unable to sleep', 'ไม่สามารถนอนได้'),
        },
    },
    'q12_Respiratory_Insufficiency': {
        'no': 12, 'domain': 'respiratory', 'domain_th': 'การหายใจ (respiratory)',
        'en': 'Respiratory Insufficiency', 'th': 'ภาวะหายใจบกพร่อง (respiratory insufficiency)',
        'levels': {
            4: ('None', 'ไม่มี'),
            3: ('Intermittent use of BiPAP', 'ใช้เครื่อง BiPAP เป็นครั้งคราว'),
            2: ('Continuous use of BiPAP', 'ใช้เครื่อง BiPAP อย่างต่อเนื่อง'),
            1: ('Continuous use of BiPAP during the night and day', 'ใช้เครื่อง BiPAP อย่างต่อเนื่อง ทั้งกลางวันและกลางคืน'),
            0: ('Invasive mechanical ventilation by intubation or tracheostomy', 'ใช้เครื่องช่วยหายใจเชิงกลแบบรุกล้ำ'),
        },
    },
}
